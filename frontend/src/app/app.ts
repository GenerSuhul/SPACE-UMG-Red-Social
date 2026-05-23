import { ChangeDetectionStrategy, Component, computed, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs/operators';
import { TokenService } from './service/auth/token';
import { UsersService } from './service/users/users';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  standalone: false,
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly tokenService = inject(TokenService);
  private readonly usersService = inject(UsersService);
  private heartbeatSub?: Subscription;

  private readonly currentUrl = signal<string>('');

  protected readonly showToolbar = computed(() => {
    const url = this.currentUrl();
    return url !== '' && !url.startsWith('/auth');
  });

  protected readonly isLoggedIn = computed(() => {
    // reactive update relies on currentUrl changes to re-evaluate token presence
    this.currentUrl(); 
    return !!this.tokenService.get();
  });

  protected readonly showMobileFab = computed(() => {
    return this.isLoggedIn() && !this.currentUrl().startsWith('/chats');
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

  ngOnInit(): void {
    // Online heartbeat: every 20 seconds
    this.heartbeatSub = interval(20000).subscribe(() => {
      if (this.tokenService.get()) {
        this.usersService.updateOnlineStatus('online').subscribe({ error: () => {} });
      }
    });

    // Initial immediate heartbeat on load
    setTimeout(() => {
      if (this.tokenService.get()) {
        this.usersService.updateOnlineStatus('online').subscribe({ error: () => {} });
      }
    }, 1000);
  }

  ngOnDestroy(): void {
    this.heartbeatSub?.unsubscribe();
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

  createPublication(): void {
    this.router.navigate(['/']).then(() => {
      setTimeout(() => {
        const trigger = document.querySelector('.publisher-trigger-btn') as HTMLElement;
        if (trigger) {
          trigger.click();
        }
      }, 150);
    });
  }

  createReel(): void {
    this.router.navigate(['/reels'], { queryParams: { create: 'true' } });
  }
}
