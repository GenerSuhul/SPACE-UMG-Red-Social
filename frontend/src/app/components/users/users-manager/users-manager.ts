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
import { MatSnackBar } from '@angular/material/snack-bar';

import { UsersService } from '../../../service/users/users';
import { PostsService } from '../../../service/posts/posts';
import { UserInterface } from '../../../models/users';
import { Post } from '../../../models/posts';
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

  posts        = signal<Post[]>([]);
  postsLoading = signal(false);

  showNewPostForm  = signal(false);
  creatingPost     = signal(false);
  selectedPostImage = signal<File | null>(null);
  postImagePreview  = signal<string | null>(null);

  updateForm:  FormGroup;
  newPostForm: FormGroup;

  private readonly usersService = inject(UsersService);
  private readonly postsService = inject(PostsService);
  private readonly dialog       = inject(MatDialog);
  private readonly router       = inject(Router);
  private readonly cdr          = inject(ChangeDetectorRef);
  private readonly snackBar     = inject(MatSnackBar);

  constructor(private fb: FormBuilder) {
    this.updateForm = this.fb.group({
      username:   ['', [Validators.required, Validators.minLength(3)]],
      email:      ['', [Validators.required, Validators.email]],
      first_name: ['', [Validators.required]],
      last_name:  ['', [Validators.required]],
      age:        [null, [Validators.required, Validators.min(18)]],
      is_active:  [true, [Validators.required]],
    });
    this.newPostForm = this.fb.group({
      content: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(5000)]],
    });
  }

  ngOnInit(): void {
    this.loading.set(true);
    this.usersService.getUser().subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.updateForm.patchValue(res.user);
        this.loading.set(false);
        this.cdr.markForCheck();
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

    this.postsLoading.set(true);
    this.postsService.getMyPosts().subscribe({
      next: (res) => {
        this.posts.set(res.posts);
        this.postsLoading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.postsLoading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  goToFollows(): void {
    this.router.navigate(['/users/follows']);
  }

  onPostDeleted(postId: string): void {
    this.posts.update(list => list.filter(p => p.id !== postId));
  }

  trackByPostId(_index: number, post: Post): string {
    return post.id;
  }

  toggleNewPostForm(): void {
    this.showNewPostForm.set(!this.showNewPostForm());
    if (!this.showNewPostForm()) {
      this.newPostForm.reset();
      this.clearPostImage();
    }
  }

  onPostImageSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedPostImage.set(file);
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        this.postImagePreview.set(reader.result as string);
        this.cdr.markForCheck();
      };
      reader.readAsDataURL(file);
    } else {
      this.postImagePreview.set(null);
    }
    input.value = '';
  }

  clearPostImage(): void {
    this.selectedPostImage.set(null);
    this.postImagePreview.set(null);
  }

  submitNewPost(): void {
    if (this.newPostForm.invalid) {
      this.newPostForm.markAllAsTouched();
      return;
    }

    this.creatingPost.set(true);
    const content: string = this.newPostForm.get('content')!.value;
    const image = this.selectedPostImage() ?? undefined;

    this.postsService.createPost(content, image).subscribe({
      next: (res) => {
        this.creatingPost.set(false);
        this.showNewPostForm.set(false);
        this.newPostForm.reset();
        this.clearPostImage();
        this.posts.update(current => [res.post, ...current]);
        this.cdr.markForCheck();
        this.snackBar.open('Publicación creada.', 'Cerrar', { duration: 3000 });
      },
      error: () => {
        this.creatingPost.set(false);
        this.cdr.markForCheck();
        this.snackBar.open('Error al crear la publicación.', 'Cerrar', { duration: 4000 });
      },
    });
  }

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

    if (!ACCEPTED_TYPES.includes(file.type)) {
      this.openDialog({
        type: 'error',
        title: 'Tipo de archivo no permitido',
        message: 'Solo se aceptan imágenes PNG, JPEG, GIF o WEBP.',
      });
      input.value = '';
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      this.openDialog({
        type: 'error',
        title: 'Archivo demasiado grande',
        message: 'El tamaño máximo permitido es 5 MB.',
      });
      input.value = '';
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    this.previewUrl.set(objectUrl);

    this.avatarUploading.set(true);
    this.usersService.updateAvatar(file).subscribe({
      next: (res) => {
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
