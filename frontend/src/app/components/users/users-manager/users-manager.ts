import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';

import { UsersService } from '../../../service/users/users';
import { UserInterface } from '../../../models/users';
import { NotificationDialog } from '../../shared/notification-dialog/notification-dialog';
import { NotificationDialogData } from '../../shared/notification-dialog/notification-dialog.model';

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

@Component({
  selector: 'app-users-manager',
  standalone: false,
  templateUrl: './users-manager.html',
  styleUrl: './users-manager.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersManager implements OnInit {
  @ViewChild('fileInput') private fileInputRef!: ElementRef<HTMLInputElement>;

  loading          = signal(true);
  editMode         = signal(false);
  avatarUploading  = signal(false);
  previewUrl       = signal<string | null>(null);
  followersCount   = signal(0);
  followingCount   = signal(0);

  user = signal<UserInterface | null>(null);

  updateForm: FormGroup;

  private readonly usersService = inject(UsersService);
  private readonly dialog       = inject(MatDialog);
  private readonly router       = inject(Router);
  private readonly cdr          = inject(ChangeDetectorRef);

  constructor(private fb: FormBuilder) {
    this.updateForm = this.fb.group({
      username:   ['', [Validators.required, Validators.minLength(3)]],
      email:      ['', [Validators.required, Validators.email]],
      first_name: ['', [Validators.required]],
      last_name:  ['', [Validators.required]],
      age:        [null, [Validators.required, Validators.min(18)]],
      is_active:  [true, [Validators.required]],
    });
  }

  ngOnInit(): void {
    this.loading.set(true);
    this.usersService.getUser().subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.updateForm.patchValue(res.user);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.openDialog({
          type: 'error',
          title: 'Error',
          message: 'No se pudo cargar la información del usuario.',
        });
      },
    });

    this.usersService.getMyFollows().subscribe({
      next: (res) => {
        this.followersCount.set(res.followers_count);
        this.followingCount.set(res.following_count);
        this.cdr.markForCheck();
      },
    });
  }

  goToFollows(): void {
    this.router.navigate(['/users/follows']);
  }

  /** Returns the data-URI to display: local preview takes priority over stored avatar. */
  get avatarSrc(): string | null {
    if (this.previewUrl()) return this.previewUrl();
    const u = this.user();
    if (u?.avatar_base64 && u.avatar_mime) {
      return `data:${u.avatar_mime};base64,${u.avatar_base64}`;
    }
    return null;
  }

  triggerFileInput(): void {
    this.fileInputRef.nativeElement.click();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file  = input.files?.[0];
    if (!file) return;

    // Validate type
    if (!ACCEPTED_TYPES.includes(file.type)) {
      this.openDialog({
        type: 'error',
        title: 'Tipo de archivo no permitido',
        message: 'Solo se aceptan imágenes PNG, JPEG, GIF o WEBP.',
      });
      input.value = '';
      return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      this.openDialog({
        type: 'error',
        title: 'Archivo demasiado grande',
        message: 'El tamaño máximo permitido es 5 MB.',
      });
      input.value = '';
      return;
    }

    // Show local preview immediately
    const objectUrl = URL.createObjectURL(file);
    this.previewUrl.set(objectUrl);

    // Upload
    this.avatarUploading.set(true);
    this.usersService.updateAvatar(file).subscribe({
      next: (res) => {
        // Revoke the object URL and display the server-returned base64
        URL.revokeObjectURL(objectUrl);
        this.previewUrl.set(null);
        this.user.set(res.user);
        this.avatarUploading.set(false);
        this.openDialog({
          type: 'success',
          title: 'Foto actualizada',
          message: 'Tu foto de perfil fue actualizada correctamente.',
        });
      },
      error: (err) => {
        URL.revokeObjectURL(objectUrl);
        this.previewUrl.set(null);
        this.avatarUploading.set(false);
        const msg = err?.error?.errors?.[0]?.message ?? 'No se pudo subir la imagen.';
        this.openDialog({ type: 'error', title: 'Error al subir imagen', message: msg });
        input.value = '';
      },
    });
  }

  toggleEditMode(enabled: boolean): void {
    this.editMode.set(enabled);
    if (!enabled) {
      this.updateForm.patchValue(this.user()!);
    }
  }

  onSubmit(): void {
    if (this.updateForm.invalid) {
      this.updateForm.markAllAsTouched();
      return;
    }

    this.usersService.updateUser(this.updateForm.value).subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.editMode.set(false);
        this.openDialog({
          type: 'success',
          title: 'Actualización exitosa',
          message: 'Tu perfil fue actualizado correctamente.',
        });
      },
      error: (error: unknown) => {
        const err = error as { error?: { message?: string } };
        this.openDialog({
          type: 'error',
          title: 'Error',
          message: err?.error?.message ?? 'Ocurrió un error inesperado.',
        });
      },
    });
  }

  private openDialog(data: NotificationDialogData): void {
    this.dialog.open(NotificationDialog, { data });
  }
}
