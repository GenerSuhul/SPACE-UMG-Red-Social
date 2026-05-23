import { inject, NgModule } from '@angular/core';
import { CanActivateFn, Router, RouterModule, Routes } from '@angular/router';
import { TokenService } from './service/auth/token';
import { Chats } from './components/chats/chats';
import { Reels } from './components/reels/reels';
import { Lives } from './components/lives/lives';

const authGuard: CanActivateFn = (route, state) => {
  const tokenService = inject(TokenService);
  const router = inject(Router);
  if (tokenService.get()) {
    return true;
  }
  router.navigate(['/auth/login']);
  return false;
};

const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./components/auth/auth-module').then(m => m.AuthModule)
  },
  {
    path: 'users',
    canActivate: [authGuard],
    loadChildren: () => import('./components/users/users-module').then(m => m.UsersModule)
  },
  {
    path: 'chats',
    component: Chats,
    canActivate: [authGuard]
  },
  {
    path: 'reels',
    component: Reels,
    canActivate: [authGuard]
  },
  {
    path: 'live',
    component: Lives,
    canActivate: [authGuard]
  },
  {
    path: '',
    canActivate: [authGuard],
    loadChildren: () => import('./components/posts-feed/posts-feed-module').then(m => m.PostsFeedModule)
  },
  {
    path: '',
    redirectTo: '/auth/login',
    pathMatch: 'full'
  }];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

