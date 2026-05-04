import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedImportModule } from '../../shared-import/shared-import-module';
import { AuthRoutingModule } from './auth-routing-module';
import { Register } from './register/register';
import { Login } from './login/login';

@NgModule({
  declarations: [Register, Login],
  imports: [CommonModule, AuthRoutingModule, ReactiveFormsModule, SharedImportModule],
})
export class AuthModule {}
