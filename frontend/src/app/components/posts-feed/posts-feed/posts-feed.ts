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
import { PostsService } from '../../../service/posts/posts';
import { Post, Pagination } from '../../../models/posts';

@Component({
  selector: 'app-posts-feed',
  standalone: false,
  templateUrl: './posts-feed.html',
  styleUrl: './posts-feed.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PostsFeed implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  posts = signal<Post[]>([]);
  pagination = signal<Pagination | null>(null);
  loadingFeed = signal(false);
  feedError = signal<string | null>(null);

  creatingPost = signal(false);
  showNewPostForm = signal(false);

  selectedFiles = signal<File[]>([]);
  postImagePreviews = signal<string[]>([]);

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
    this.loadPosts(1);
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

    this.creatingPost.set(true);
    const content: string = this.newPostForm.get('content')!.value;
    const files = this.selectedFiles().length ? this.selectedFiles() : undefined;

    this.postsService.createPost(content, files)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.creatingPost.set(false);
          this.showNewPostForm.set(false);
          this.newPostForm.reset();
          this.clearPostImages();
          // Prepend new post at the top
          this.posts.update(current => [res.post, ...current]);
          this.snackBar.open('Publicacion creada.', 'Cerrar', { duration: 3000 });
        },
        error: () => {
          this.creatingPost.set(false);
          this.snackBar.open('Error al crear la publicacion.', 'Cerrar', { duration: 4000 });
        },
      });
  }

  onPostDeleted(postId: string): void {
    this.posts.update(current => current.filter(p => p.id !== postId));
    this.snackBar.open('Publicacion eliminada.', 'Cerrar', { duration: 3000 });
  }

  trackByPostId(_index: number, post: Post): string {
    return post.id;
  }
}
