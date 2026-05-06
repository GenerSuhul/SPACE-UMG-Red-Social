import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subject, switchMap, takeUntil } from 'rxjs';

import { UsersService } from '../../../service/users/users';
import { PublicUserInterface } from '../../../models/users';

@Component({
  selector: 'app-user-view',
  standalone: false,
  templateUrl: './user-view.html',
  styleUrl: './user-view.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserView implements OnInit, OnDestroy {
  loading       = signal(true);
  notFound      = signal(false);
  followLoading = signal(false);
  user          = signal<PublicUserInterface | null>(null);
  isFollowing   = signal(false);
  followersCount = signal(0);

  private readonly route        = inject(ActivatedRoute);
  private readonly usersService = inject(UsersService);
  private readonly cdr          = inject(ChangeDetectorRef);

  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.route.paramMap.pipe(
      switchMap(params => {
        const id = params.get('id') ?? '';
        this.loading.set(true);
        this.notFound.set(false);
        this.user.set(null);
        this.isFollowing.set(false);
        this.followersCount.set(0);
        this.cdr.markForCheck();
        return this.usersService.getUserById(id);
      }),
      takeUntil(this.destroy$),
    ).subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.isFollowing.set(res.user.is_following ?? false);
        this.followersCount.set(res.user.followers_count ?? 0);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: (err: unknown) => {
        this.loading.set(false);
        if ((err as { status?: number })?.status === 404) {
          this.notFound.set(true);
        }
        this.cdr.markForCheck();
      },
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onToggleFollow(): void {
    const u = this.user();
    if (!u || this.followLoading()) return;
    this.followLoading.set(true);
    this.usersService.toggleFollow(u.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => {
        this.isFollowing.set(res.action === 'followed');
        this.followersCount.set(res.followers_count);
        this.followLoading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.followLoading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  get avatarSrc(): string | null {
    const u = this.user();
    if (u?.avatar_base64 && u.avatar_mime) {
      return `data:${u.avatar_mime};base64,${u.avatar_base64}`;
    }
    return null;
  }
}
