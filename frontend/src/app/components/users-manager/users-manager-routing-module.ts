import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UsersManager } from './users-manager';

const routes: Routes = [
  { path: '', component: UsersManager }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class UsersManagerRoutingModule {}
