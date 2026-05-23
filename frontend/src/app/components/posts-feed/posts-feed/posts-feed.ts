import {
  Component,
  OnInit,
  ChangeDetectionStrategy,
  signal,
  DestroyRef,
  inject,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { PostsService } from '../../../service/posts/posts';
import { UsersService } from '../../../service/users/users';
import { ChatsService } from '../../../service/chats/chats';
import { UploadService } from '../../../service/upload';
import { Post, Pagination } from '../../../models/posts';

const DEFAULT_STORIES = [
  {
    id: 'story-sim-1',
    author_username: 'sofia_sistemas',
    author_avatar_url: '',
    media_url: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=600&q=80',
    type: 'image'
  },
  {
    id: 'story-sim-2',
    author_username: 'mario_galvez',
    author_avatar_url: '',
    media_url: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80',
    type: 'image'
  },
  {
    id: 'story-sim-3',
    author_username: 'umg_central',
    author_avatar_url: '',
    media_url: 'https://assets.mixkit.co/videos/preview/mixkit-software-developer-working-on-his-computer-34285-large.mp4',
    type: 'video'
  }
];

@Component({
  selector: 'app-posts-feed',
  standalone: false,
  templateUrl: './posts-feed.html',
  styleUrl: './posts-feed.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PostsFeed implements OnInit {
  private readonly destroyRef   = inject(DestroyRef);
  private readonly usersService = inject(UsersService);
  private readonly chatsService = inject(ChatsService);
  private readonly router       = inject(Router);
  private readonly uploadService = inject(UploadService);

  readonly currentUser$ = this.usersService.currentUser$;
  recommendations       = signal<any[]>([]);
  loadingRecommendations = signal(false);
  activeChats           = signal<any[]>([]);

  // Stories signals
  stories = signal<any[]>([]);
  uploadingStory = signal(false);
  storyProgress = signal(0);
  activeStoryIndex = signal<number | null>(null);
  storyViewerProgress = signal(0);
  private storyInterval: any = null;

  posts = signal<Post[]>([]);
  pagination = signal<Pagination | null>(null);
  loadingFeed = signal(false);
  feedError = signal<string | null>(null);

  creatingPost = signal(false);
  showNewPostForm = signal(false);

  selectedFiles = signal<File[]>([]);
  postImagePreviews = signal<string[]>([]);
  uploadingFiles = signal(false);
  uploadProgress = signal<number | null>(null);

  newPostForm: FormGroup;

  constructor(
    private postsService: PostsService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
  ) {
    this.newPostForm = this.fb.group({
      content: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(5000)]],
    });
  }

  ngOnInit(): void {
    // Force compilation trigger
    this.loadPosts(1);
    this.loadRecommendations();
    this.loadActiveChats();
    this.loadStories();
    this.usersService.getUser().subscribe();
  }

  loadRecommendations(): void {
    this.loadingRecommendations.set(true);
    this.usersService.getRecommendations(5)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          if (res && res.users) {
            this.recommendations.set(res.users);
          }
          this.loadingRecommendations.set(false);
        },
        error: () => {
          this.loadingRecommendations.set(false);
        }
      });
  }

  loadActiveChats(): void {
    this.chatsService.listMyChats()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          if (res && res.chats) {
            this.activeChats.set(res.chats);
          }
        },
        error: () => {}
      });
  }

  followUser(userId: string): void {
    this.usersService.toggleFollow(userId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          if (res.ok && res.action === 'followed') {
            this.snackBar.open('¡Ahora sigues a este alumno!', 'Cerrar', { duration: 3000 });
            this.recommendations.update(recs => recs.filter(u => u.id !== userId));
            this.usersService.getUser().subscribe();
          }
        },
        error: () => {
          this.snackBar.open('Error al seguir al alumno.', 'Cerrar', { duration: 4000 });
        }
      });
  }

  startChatWith(userId: string): void {
    this.chatsService.getOrCreateChat(userId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          if (res && res.ok) {
            this.router.navigate(['/chats'], { queryParams: { active: res.chat.id } });
          }
        },
        error: () => {
          this.snackBar.open('No se pudo iniciar el chat.', 'Cerrar', { duration: 4000 });
        }
      });
  }

  loadPosts(page: number): void {
    this.loadingFeed.set(true);
    this.feedError.set(null);

    this.postsService.listPosts(page, 20)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.posts.set(res.posts);
          this.pagination.set(res.pagination);
          this.loadingFeed.set(false);
        },
        error: () => {
          this.feedError.set('No se pudo cargar el feed. Intenta de nuevo.');
          this.loadingFeed.set(false);
        },
      });
  }

  goToPage(page: number): void {
    const p = this.pagination();
    if (!p) return;
    const totalPages = p.total_pages ?? 1;
    if (page < 1 || page > totalPages) return;
    this.loadPosts(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  get currentPage(): number {
    return this.pagination()?.page ?? 1;
  }

  get totalPages(): number {
    return this.pagination()?.total_pages ?? 1;
  }

  toggleNewPostForm(): void {
    this.showNewPostForm.set(!this.showNewPostForm());
    if (!this.showNewPostForm()) {
      this.newPostForm.reset();
      this.clearPostImages();
    }
  }

  onPostImageSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files ?? []).slice(0, 5);
    this.selectedFiles.set(files);
    this.postImagePreviews.set([]);

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = () => {
        this.postImagePreviews.update(prev => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });
    input.value = '';
  }

  removePostImage(index: number): void {
    this.selectedFiles.update(files => files.filter((_, i) => i !== index));
    this.postImagePreviews.update(prev => prev.filter((_, i) => i !== index));
  }

  clearPostImages(): void {
    this.selectedFiles.set([]);
    this.postImagePreviews.set([]);
  }

  submitNewPost(): void {
    if (this.newPostForm.invalid) {
      this.newPostForm.markAllAsTouched();
      return;
    }

    const content: string = this.newPostForm.get('content')!.value;
    const files = this.selectedFiles();

    if (files.length > 0) {
      this.creatingPost.set(true);
      this.uploadingFiles.set(true);
      this.uploadProgress.set(0);

      let completedUploads = 0;
      const uploadedUrls: string[] = [];
      
      const performUploads = () => {
        if (completedUploads < files.length) {
          const currentFile = files[completedUploads];
          this.uploadService.uploadFile(currentFile, 'post').subscribe({
            next: (event: HttpEvent<any>) => {
              if (event.type === HttpEventType.UploadProgress && event.total) {
                const percent = Math.round((event.loaded / event.total) * 100);
                const basePercent = (completedUploads / files.length) * 100;
                const fileShare = 100 / files.length;
                this.uploadProgress.set(Math.round(basePercent + (percent * fileShare / 100)));
              } else if (event.type === HttpEventType.Response) {
                if (event.body && event.body.ok && event.body.url) {
                  uploadedUrls.push(event.body.url);
                }
              }
            },
            error: (err) => {
              this.creatingPost.set(false);
              this.uploadingFiles.set(false);
              this.uploadProgress.set(null);
              this.snackBar.open('Error al subir imágenes a R2: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 5000 });
            },
            complete: () => {
              completedUploads++;
              performUploads();
            }
          });
        } else {
          this.uploadProgress.set(null);
          this.uploadingFiles.set(false);
          this.createPostWithMedia(content, uploadedUrls);
        }
      };

      performUploads();
    } else {
      this.creatingPost.set(true);
      this.createPostWithMedia(content, []);
    }
  }

  private createPostWithMedia(content: string, mediaUrls: string[]): void {
    this.postsService.createPost(content, [], mediaUrls)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.creatingPost.set(false);
          this.showNewPostForm.set(false);
          this.newPostForm.reset();
          this.clearPostImages();
          this.posts.update(current => [res.post, ...current]);
          this.snackBar.open('Publicación creada.', 'Cerrar', { duration: 3000 });
        },
        error: (err) => {
          this.creatingPost.set(false);
          this.snackBar.open('Error al crear la publicación: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 4000 });
        },
      });
  }

  onPostDeleted(postId: string): void {
    this.posts.update(current => current.filter(p => p.id !== postId));
    this.snackBar.open('Publicacion eliminada.', 'Cerrar', { duration: 3000 });
  }

  onPostUpdated(updatedPost: Post): void {
    this.posts.update(current => current.map(p => p.id === updatedPost.id ? updatedPost : p));
  }

  trackByPostId(_index: number, post: Post): string {
    return post.id;
  }

  // ── STORIES MVP IMPLEMENTATION ──

  loadStories(): void {
    this.postsService.listStories(1, 20).subscribe({
      next: (res) => {
        const dbStories = (res.posts || []).map(p => ({
          id: p.id,
          author_username: p.author_username,
          author_avatar_url: p.author_avatar_url,
          media_url: p.media_urls?.[0],
          type: this.isStoryVideo(p.media_urls?.[0]) ? 'video' : 'image'
        }));
        
        // Merge db stories with default mock ones to guarantee a beautiful display
        this.stories.set([
          ...dbStories,
          ...DEFAULT_STORIES
        ]);
      },
      error: () => {
        this.stories.set(DEFAULT_STORIES);
      }
    });
  }

  isStoryVideo(url?: string): boolean {
    if (!url) return false;
    const cleanUrl = url.split('?')[0].toLowerCase();
    return cleanUrl.endsWith('.mp4') || 
           cleanUrl.endsWith('.mov') || 
           cleanUrl.endsWith('.webm') || 
           cleanUrl.includes('/reels/') || 
           cleanUrl.includes('/reel/');
  }

  onStoryFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (!file) return;

    // Limit size: 50MB
    const limitBytes = 50 * 1024 * 1024;
    if (file.size > limitBytes) {
      this.snackBar.open('La historia excede el límite permitido de 50MB.', 'Cerrar', { duration: 4000 });
      return;
    }

    // Validate mime type
    const allowedImages = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    const allowedVideos = ['video/mp4', 'video/quicktime', 'video/webm'];
    if (!allowedImages.includes(file.type) && !allowedVideos.includes(file.type)) {
      this.snackBar.open('Formato no soportado. Use imágenes o videos.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.uploadingStory.set(true);
    this.storyProgress.set(0);

    this.uploadService.uploadFile(file, 'story').subscribe({
      next: (ev: HttpEvent<any>) => {
        if (ev.type === HttpEventType.UploadProgress && ev.total) {
          this.storyProgress.set(Math.round((ev.loaded / ev.total) * 100));
        } else if (ev.type === HttpEventType.Response) {
          if (ev.body && ev.body.ok && ev.body.url) {
            this.publishStory(ev.body.url);
          }
        }
      },
      error: (err) => {
        this.uploadingStory.set(false);
        this.snackBar.open('Error al subir historia a R2: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 5000 });
      }
    });
    input.value = '';
  }

  private publishStory(mediaUrl: string): void {
    this.postsService.createPost('Story', [], [mediaUrl], 'story').subscribe({
      next: (res) => {
        this.uploadingStory.set(false);
        this.snackBar.open('¡Historia publicada con éxito!', 'Cerrar', { duration: 3000 });
        this.loadStories();
      },
      error: (err) => {
        this.uploadingStory.set(false);
        this.snackBar.open('Error al publicar historia: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 4000 });
      }
    });
  }

  openStory(index: number): void {
    this.activeStoryIndex.set(index);
    this.storyViewerProgress.set(0);
    if (this.storyInterval) {
      clearInterval(this.storyInterval);
    }
    
    this.storyInterval = setInterval(() => {
      const current = this.storyViewerProgress();
      if (current < 100) {
        this.storyViewerProgress.set(current + 2);
      } else {
        this.nextStory();
      }
    }, 100); // 100ms ticks, takes 5s (50 ticks of +2%) to complete
  }

  nextStory(): void {
    const nextIdx = (this.activeStoryIndex() ?? 0) + 1;
    if (nextIdx < this.stories().length) {
      this.openStory(nextIdx);
    } else {
      this.closeStory();
    }
  }

  prevStory(): void {
    const prevIdx = (this.activeStoryIndex() ?? 0) - 1;
    if (prevIdx >= 0) {
      this.openStory(prevIdx);
    } else {
      this.openStory(0);
    }
  }

  closeStory(): void {
    this.activeStoryIndex.set(null);
    this.storyViewerProgress.set(0);
    if (this.storyInterval) {
      clearInterval(this.storyInterval);
      this.storyInterval = null;
    }
  }
}
