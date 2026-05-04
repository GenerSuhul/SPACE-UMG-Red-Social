import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Register } from './register/register';
import { Login } from './login/login';

const routes: Routes = [
  {
    path: 'register',
    component: Register
  },
  {
    path: 'login',
    component: Login
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AuthRoutingModule {}
