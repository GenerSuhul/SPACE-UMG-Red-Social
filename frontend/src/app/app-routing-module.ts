import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./components/auth/auth-module').then(m => m.AuthModule)
  },
  {
    path: 'users',
    loadChildren: () => import('./components/users-manager/users-manager-module').then(m => m.UsersManagerModule)
  },
  {
    path: 'feed',
    loadChildren: () => import('./components/posts-feed/posts-feed-module').then(m => m.PostsFeedModule)
  },
  {
    path: '',
    redirectTo: '/auth/register',
    pathMatch: 'full'
  }];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
