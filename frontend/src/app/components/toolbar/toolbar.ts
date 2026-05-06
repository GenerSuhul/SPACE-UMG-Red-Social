import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { TokenService } from '../../service/auth/token';
import { Auth } from '../../service/auth/auth';
import { UsersService } from '../../service/users/users';

@Component({
  selector: 'app-toolbar',
  standalone: false,
  templateUrl: './toolbar.html',
  styleUrl: './toolbar.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Toolbar {
  private readonly router       = inject(Router);
  private readonly tokenService = inject(TokenService);
  private readonly authService  = inject(Auth);
  readonly usersService         = inject(UsersService);

  /** Exposed for the async pipe in the template. */
  readonly currentUser$ = this.usersService.currentUser$;

  logout(): void {
    this.authService.logoutUser().subscribe({
      next: () => this.clearAndRedirect(),
      error: () => this.clearAndRedirect(),
    });
  }

  private clearAndRedirect(): void {
    this.tokenService.clear();
    this.router.navigate(['/auth/login']);
  }

  goToFeed(): void {
    this.router.navigate(['/feed']);
  }

  goToUsers(): void {
    this.router.navigate(['/users']);
  }
}
