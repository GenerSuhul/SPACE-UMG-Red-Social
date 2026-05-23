import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs/operators';
import { TokenService } from './service/auth/token';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  standalone: false,
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  private readonly router = inject(Router);
  private readonly tokenService = inject(TokenService);

  private readonly currentUrl = signal<string>('');

  protected readonly showToolbar = computed(
    () => !this.currentUrl().startsWith('/auth')
  );

  protected readonly isLoggedIn = computed(() => {
    // reactive update relies on currentUrl changes to re-evaluate token presence
    this.currentUrl(); 
    return !!this.tokenService.get();
  });

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed()
      )
      .subscribe((event) => {
        this.currentUrl.set(event.urlAfterRedirects);
      });
  }

  isActive(route: string): boolean {
    if (route === '/') {
      return this.currentUrl() === '/' || this.currentUrl() === '/feed' || this.currentUrl().startsWith('/?post=');
    }
    return this.currentUrl().startsWith(route);
  }

  navigate(route: string): void {
    this.router.navigate([route]);
  }

  triggerMobilePublish(): void {
    this.router.navigate(['/']).then(() => {
      // If we are on the feed, trigger the publisher expansion
      setTimeout(() => {
        const trigger = document.querySelector('.publisher-trigger-btn') as HTMLElement;
        if (trigger) {
          trigger.click();
        }
      }, 100);
    });
  }
}
