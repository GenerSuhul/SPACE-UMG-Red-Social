import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserLoginInterface } from '../../../models/auth';
import { Auth } from '../../../service/auth/auth';
import { TokenService } from '../../../service/auth/token';
import { Router } from '@angular/router';

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
          this.router.navigate(["/users"])
        }
      }, (error) => {
        console.error("Error en login")
      }
    )
  }
}
