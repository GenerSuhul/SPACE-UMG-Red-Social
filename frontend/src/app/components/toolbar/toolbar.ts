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
} from 'rxjs';

import { TokenService } from '../../service/auth/token';
import { Auth } from '../../service/auth/auth';
import { UsersService } from '../../service/users/users';
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

  private readonly router       = inject(Router);
  private readonly tokenService = inject(TokenService);
  private readonly authService  = inject(Auth);
  private readonly cdr          = inject(ChangeDetectorRef);
  readonly usersService         = inject(UsersService);

  readonly currentUser$ = this.usersService.currentUser$;

  readonly searchControl = new FormControl('', { nonNullable: true });
  searchResults: PublicUserInterface[] = [];
  showDropdown = false;

  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
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
}
