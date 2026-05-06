import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserLoginInterface } from '../../../models/auth';
import { Auth } from '../../../service/auth/auth';
import { TokenService } from '../../../service/auth/token';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { NotificationDialog } from '../../shared/notification-dialog/notification-dialog';
import { NotificationDialogData } from '../../shared/notification-dialog/notification-dialog.model';

@Component({
  selector: 'app-login',
  standalone: false,
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {

  loginForm: FormGroup;

  hidePass = signal(true);

  constructor(
    private fb: FormBuilder,
    private authService: Auth,
    private tokenService: TokenService,
    private router: Router,
    private dialog: MatDialog,
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(8)]]
    });
  }

  togglePass() {
    this.hidePass.update(value => !value);
  }

  onSubmit(): void {
    if (!this.loginForm.valid) return

    const userLogin: UserLoginInterface = this.loginForm.value;

    this.authService.loginUser(userLogin).subscribe(
      (value) => {
        if (value) {
          this.tokenService.set(value.token);
          this.router.navigate(["/"])
        }
      }, (error) => {
        const message: string = error?.error?.message ?? 'Ocurrió un error inesperado.';
        this.dialog.open<NotificationDialog, NotificationDialogData>(NotificationDialog, {
          data: { type: 'error', title: 'Error', message },
          width: '400px',
        });
      }
    )
  }
}
