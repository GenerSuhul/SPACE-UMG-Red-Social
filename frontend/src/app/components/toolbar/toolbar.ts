import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnInit,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';
import { FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import {
  Subject,
  debounceTime,
  distinctUntilChanged,
  switchMap,
  of,
  takeUntil,
  catchError,
  interval,
  startWith,
} from 'rxjs';

import { TokenService } from '../../service/auth/token';
import { Auth } from '../../service/auth/auth';
import { UsersService } from '../../service/users/users';
import { NotificationsService } from '../../service/notifications/notifications';
import { PublicUserInterface } from '../../models/users';

@Component({
  selector: 'app-toolbar',
  standalone: false,
  templateUrl: './toolbar.html',
  styleUrl: './toolbar.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Toolbar implements OnInit, OnDestroy {
  @ViewChild('searchWrapper') private searchWrapperRef!: ElementRef<HTMLElement>;

  private readonly router             = inject(Router);
  private readonly tokenService       = inject(TokenService);
  private readonly authService        = inject(Auth);
  private readonly cdr                = inject(ChangeDetectorRef);
  readonly usersService               = inject(UsersService);
  private readonly notificationsService = inject(NotificationsService);

  readonly currentUser$ = this.usersService.currentUser$;

  get isLoggedIn(): boolean {
    return !!this.tokenService.get();
  }

  readonly searchControl = new FormControl('', { nonNullable: true });
  searchResults: PublicUserInterface[] = [];
  showDropdown = false;

  notifications: any[] = [];
  unreadNotificationsCount = 0;

  private readonly destroy$ = new Subject<void>();

  isDarkMode = false;

  ngOnInit(): void {
    this.isDarkMode = localStorage.getItem('theme') === 'dark';
    document.body.classList.toggle('dark-mode', this.isDarkMode);
    this.cdr.markForCheck();
    this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        const trimmed = query.trim();
        if (!trimmed) {
          this.searchResults = [];
          this.showDropdown  = false;
          this.cdr.markForCheck();
          return of(null);
        }
        return this.usersService.searchUsers(trimmed).pipe(
          catchError(() => of(null)),
        );
      }),
      takeUntil(this.destroy$),
    ).subscribe(res => {
      if (res) {
        this.searchResults = res.users;
        this.showDropdown  = res.users.length > 0;
      } else if (this.searchControl.value.trim() === '') {
        this.searchResults = [];
        this.showDropdown  = false;
      }
      this.cdr.markForCheck();
    });

    // Fetch authenticated user details to populate currentUser$ state
    if (this.tokenService.get()) {
      this.usersService.getUser().subscribe({
        next: () => this.cdr.markForCheck(),
        error: () => {}
      });
    }

    // Poll notifications every 7 seconds to simulate real-time notification push
    interval(7000)
      .pipe(
        startWith(0),
        switchMap(() => {
          if (this.tokenService.get()) {
            return this.notificationsService.listNotifications(10).pipe(
              catchError(() => of(null))
            );
          }
          return of(null);
        }),
        takeUntil(this.destroy$)
      )
      .subscribe((res) => {
        if (res && res.ok) {
          this.notifications = res.notifications;
          this.unreadNotificationsCount = res.notifications.filter((n: any) => !n.is_read).length;
          this.cdr.markForCheck();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  selectUser(user: PublicUserInterface): void {
    this.closeSearch();
    const myId = this.tokenService.getCurrentUserId();
    if (user.id === myId) {
      this.router.navigate(['/users']);
    } else {
      this.router.navigate(['/users', user.id]);
    }
  }

  closeSearch(): void {
    this.searchControl.setValue('', { emitEvent: false });
    this.searchResults = [];
    this.showDropdown  = false;
    this.cdr.markForCheck();
  }

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
    this.router.navigate(['/']);
  }

  goToMyProfile(): void {
    this.router.navigate(['/users']);
  }

  goToChats(): void {
    this.router.navigate(['/chats']);
  }

  goToReels(): void {
    this.router.navigate(['/reels']);
  }

  goToLive(): void {
    this.router.navigate(['/live']);
  }

  toggleDarkMode(): void {
    this.isDarkMode = !this.isDarkMode;
    document.body.classList.toggle('dark-mode', this.isDarkMode);
    localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
    this.cdr.markForCheck();
  }

  onNotificationsMenuOpen(): void {
    this.loadNotifications();
  }

  loadNotifications(): void {
    if (!this.tokenService.get()) return;
    this.notificationsService.listNotifications(10).subscribe({
      next: (res) => {
        if (res.ok) {
          this.notifications = res.notifications;
          this.unreadNotificationsCount = res.notifications.filter((n: any) => !n.is_read).length;
          this.cdr.markForCheck();
        }
      }
    });
  }

  markNotificationsRead(): void {
    this.notificationsService.markAllRead().subscribe({
      next: (res) => {
        if (res.ok) {
          this.notifications = this.notifications.map((n) => ({ ...n, is_read: true }));
          this.unreadNotificationsCount = 0;
          this.cdr.markForCheck();
        }
      }
    });
  }

  handleNotificationClick(notif: any): void {
    if (notif.post_id) {
      this.router.navigate(['/'], { queryParams: { post: notif.post_id } });
    } else if (notif.sender_id) {
      this.router.navigate(['/users', notif.sender_id]);
    }
  }

  getNotificationIcon(type: string): string {
    switch (type) {
      case 'follow': return 'person_add';
      case 'like': return 'favorite';
      case 'comment': return 'comment';
      case 'mention': return 'alternate_email';
      case 'share': return 'share';
      default: return 'notifications';
    }
  }

  parseNotificationDate(date: any): any {
    if (!date) return new Date();
    if (typeof date === 'object') {
      if (date.$date) {
        if (typeof date.$date === 'object' && date.$date.$numberLong) {
          return new Date(Number(date.$date.$numberLong));
        }
        return new Date(date.$date);
      }
      if (date instanceof Date) return date;
      if (typeof date.getTime === 'function') return date;
      return new Date();
    }
    return date;
  }
}
