import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, switchMap, takeUntil } from 'rxjs';

import { UsersService } from '../../../service/users/users';
import { PostsService } from '../../../service/posts/posts';
import { ChatsService } from '../../../service/chats/chats';
import { TokenService } from '../../../service/auth/token';
import { UploadService } from '../../../service/upload';
import { Auth } from '../../../service/auth/auth';
import { MatSnackBar } from '@angular/material/snack-bar';
import { PublicUserInterface } from '../../../models/users';
import { Post } from '../../../models/posts';

@Component({
  selector: 'app-user-view',
  standalone: false,
  templateUrl: './user-view.html',
  styleUrl: './user-view.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserView implements OnInit, OnDestroy {
  loading        = signal(true);
  notFound       = signal(false);
  followLoading  = signal(false);
  user           = signal<PublicUserInterface | null>(null);
  isFollowing    = signal(false);
  followersCount = signal(0);
  viewMode       = signal<'grid' | 'feed' | 'info'>('grid');

  posts        = signal<Post[]>([]);
  postsLoading = signal(false);

  uploadingCover = signal(false);
  myId = '';

  private readonly route        = inject(ActivatedRoute);
  private readonly router       = inject(Router);
  private readonly usersService = inject(UsersService);
  private readonly postsService = inject(PostsService);
  private readonly chatsService = inject(ChatsService);
  private readonly tokenService = inject(TokenService);
  private readonly uploadService = inject(UploadService);
  private readonly authService = inject(Auth);
  private readonly snackBar     = inject(MatSnackBar);
  private readonly cdr          = inject(ChangeDetectorRef);

  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.myId = this.tokenService.getCurrentUserId() || '';
    this.route.paramMap.pipe(
      switchMap(params => {
        const id = params.get('id') ?? '';
        this.loading.set(true);
        this.notFound.set(false);
        this.user.set(null);
        this.isFollowing.set(false);
        this.followersCount.set(0);
        this.posts.set([]);
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
        this.loadUserPosts(res.user.id);
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

  private loadUserPosts(userId: string): void {
    this.postsLoading.set(true);
    this.cdr.markForCheck();
    this.postsService.getUserPosts(userId).pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => {
        this.posts.set(res.posts);
        this.postsLoading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.postsLoading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  onPostDeleted(postId: string): void {
    this.posts.update(list => list.filter(p => p.id !== postId));
  }

  onPostUpdated(updatedPost: Post): void {
    this.posts.update(list => list.map(p => p.id === updatedPost.id ? updatedPost : p));
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

  trackByPostId(_index: number, post: Post): string {
    return post.id;
  }

  get avatarSrc(): string | null {
    const u = this.user();
    if (u?.avatar_url) {
      return u.avatar_url;
    }
    if (u?.avatar_base64 && u.avatar_mime) {
      return `data:${u.avatar_mime};base64,${u.avatar_base64}`;
    }
    return null;
  }

  getTotalReactions(post: Post): number {
    if (!post || !post.reactions_count) return 0;
    const rc = post.reactions_count;
    return (rc.like || 0) + (rc.love || 0) + (rc.haha || 0) + (rc.wow || 0) + (rc.sad || 0) + (rc.angry || 0);
  }

  selectGridPost(postId: string): void {
    this.viewMode.set('feed');
    this.cdr.detectChanges();

    setTimeout(() => {
      const element = document.getElementById('post-' + postId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('highlight-glow');
        setTimeout(() => {
          element.classList.remove('highlight-glow');
        }, 2000);
      }
    }, 100);
  }

  onStartChat(): void {
    const u = this.user();
    if (!u) return;
    this.chatsService.getOrCreateChat(u.id).subscribe({
      next: (res) => {
        if (res.ok && res.chat) {
          this.router.navigate(['/chats']);
        }
      },
      error: () => {}
    });
  }

  isMe(): boolean {
    const u = this.user();
    return !!u && this.myId === u.id;
  }

  get coverSrc(): string | null {
    const u = this.user();
    if (u?.cover_url) {
      return u.cover_url;
    }
    if (u?.cover_base64 && u.cover_mime) {
      return `data:${u.cover_mime};base64,${u.cover_base64}`;
    }
    return null;
  }

  onCoverSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (!file) return;

    // Limit to 10MB
    const limitBytes = 10 * 1024 * 1024;
    if (file.size > limitBytes) {
      this.snackBar.open('La portada excede el límite permitido de 10MB.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.uploadingCover.set(true);
    this.cdr.markForCheck();

    // Upload using post media endpoint to preserve higher width quality (1080px)
    this.uploadService.uploadFile(file, 'post').subscribe({
      next: (ev: any) => {
        if (ev.type === 4) { // HttpEventType.Response is 4
          if (ev.body && ev.body.ok && ev.body.url) {
            const coverUrl = ev.body.url;
            this.updateProfileCover(coverUrl);
          }
        }
      },
      error: (err: any) => {
        this.uploadingCover.set(false);
        this.cdr.markForCheck();
        this.snackBar.open('Error al subir la portada a R2: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 5000 });
      }
    });
    input.value = '';
  }

  private updateProfileCover(coverUrl: string): void {
    // Send PUT/PATCH request to update cover_url in MongoDB
    this.usersService.updateProfile({ cover_url: coverUrl } as any).subscribe({
      next: (res) => {
        this.uploadingCover.set(false);
        if (res.ok) {
          // Update local state dynamically
          const u = this.user();
          if (u) {
            this.user.set({ ...u, cover_url: coverUrl });
          }
          this.snackBar.open('¡Foto de portada actualizada con éxito!', 'Cerrar', { duration: 3000 });
          this.cdr.markForCheck();
        }
      },
      error: (err: any) => {
        this.uploadingCover.set(false);
        this.cdr.markForCheck();
        this.snackBar.open('Error al guardar la portada: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 4000 });
      }
    });
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
}
