import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';

import { UsersService } from '../../../service/users/users';
import { FollowUser } from '../../../models/users';

@Component({
  selector: 'app-my-follows',
  standalone: false,
  templateUrl: './my-follows.html',
  styleUrl: './my-follows.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MyFollows implements OnInit {
  loading          = signal(true);
  followersCount   = signal(0);
  followingCount   = signal(0);
  followers        = signal<FollowUser[]>([]);
  following        = signal<FollowUser[]>([]);
  unfollowingId    = signal<string | null>(null);

  private readonly usersService = inject(UsersService);
  private readonly router       = inject(Router);
  private readonly cdr          = inject(ChangeDetectorRef);

  ngOnInit(): void {
    this.loadFollows();
  }

  private loadFollows(): void {
    this.loading.set(true);
    this.usersService.getMyFollows().subscribe({
      next: (res) => {
        this.followers.set(res.followers);
        this.following.set(res.following);
        this.followersCount.set(res.followers_count);
        this.followingCount.set(res.following_count);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  onUnfollow(user: FollowUser): void {
    if (this.unfollowingId()) return;
    this.unfollowingId.set(user.id);
    this.usersService.toggleFollow(user.id).subscribe({
      next: () => {
        this.following.update(list => list.filter(u => u.id !== user.id));
        this.followingCount.update(n => n - 1);
        this.unfollowingId.set(null);
        this.cdr.markForCheck();
      },
      error: () => {
        this.unfollowingId.set(null);
        this.cdr.markForCheck();
      },
    });
  }

  goToProfile(userId: string): void {
    this.router.navigate(['/users', userId]);
  }

  goBack(): void {
    this.router.navigate(['/users']);
  }
}
