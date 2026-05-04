import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserLoginInterface } from '../../../models/auth';
import { Auth } from '../../../service/auth/auth';

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
    private authService: Auth
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
          // TODO implementar guardado de token en el local storage
          console.log("Logeado");
        }
      }, (error) => {
        console.error("Error en login")
      }
    )
  }
}
