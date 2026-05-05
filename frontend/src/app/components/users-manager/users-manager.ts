import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';

import { UsersService } from '../../service/users/users';
import { NotificationDialog } from '../shared/notification-dialog/notification-dialog';
import { NotificationDialogData } from '../shared/notification-dialog/notification-dialog.model';

@Component({
  selector: 'app-users-manager',
  standalone: false,
  templateUrl: './users-manager.html',
  styleUrl: './users-manager.css',
})
export class UsersManager implements OnInit {
  loading = true;

  updateForm: FormGroup = this.fb.group({
    username:   ['', [Validators.required, Validators.minLength(3)]],
    email:      ['', [Validators.required, Validators.email]],
    first_name: ['', [Validators.required]],
    last_name:  ['', [Validators.required]],
    age:        [null, [Validators.required, Validators.min(18)]],
    is_active:  [true, [Validators.required]],
  });

  constructor(
    private fb: FormBuilder,
    private usersService: UsersService,
    private dialog: MatDialog,
  ) {}

  ngOnInit(): void {
    this.loading = true;
    this.usersService.getUser().subscribe({
      next: (res) => {
        this.updateForm.patchValue(res.user);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.openDialog({
          type: 'error',
          title: 'Error',
          message: 'No se pudo cargar la información del usuario.',
        });
      },
    });
  }

  onSubmit(): void {
    if (this.updateForm.invalid) {
      this.updateForm.markAllAsTouched();
      return;
    }

    this.usersService.updateUser(this.updateForm.value).subscribe({
      next: () => {
        this.openDialog({
          type: 'success',
          title: 'Actualización exitosa',
          message: 'Tu perfil fue actualizado correctamente.',
        });
      },
      error: (error: any) => {
        this.openDialog({
          type: 'error',
          title: 'Error',
          message: error?.error?.message ?? 'Ocurrió un error inesperado.',
        });
      },
    });
  }

  private openDialog(data: NotificationDialogData): void {
    this.dialog.open(NotificationDialog, { data });
  }
}
