import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedImportModule } from '../../shared-import/shared-import-module';
import { AuthRoutingModule } from './auth-routing-module';
import { Register } from './register/register';

@NgModule({
  declarations: [Register],
  imports: [
    CommonModule,
    AuthRoutingModule,
    ReactiveFormsModule,
    SharedImportModule
  ],
})
export class AuthModule {}
