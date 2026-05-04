import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserRegisterInterface } from '../../../models/auth';
import { Auth } from '../../../service/auth/auth';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: false,
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {

  registerForm: FormGroup;
  hidePass = signal(true);

  constructor(
    private fb: FormBuilder,
    private authService: Auth,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['',  [Validators.required, Validators.minLength(8)]],
      email: ['', [Validators.required, Validators.email]],
      age: [0, [Validators.required, Validators.min(18)]],
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]]
    });
  }

  togglePassword() {
    this.hidePass.update(value => !value);
  }

  onSubmit() {
    if (!this.registerForm.valid) return

    // console.log("Envio correcto")

    const userRegister: UserRegisterInterface = this.registerForm.value;

    this.authService.registerUser(userRegister).subscribe(
      (value) => {
        if (value) {
          this.router.navigate(['/']);
        }
      }, (error) => {
        console.error("Error en registrar usuario");
      }
    )
  }

}
