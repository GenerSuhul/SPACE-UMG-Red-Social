import {
  Component,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
  signal,
  DestroyRef,
  inject,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { PostsService } from '../../../service/posts/posts';
import { TokenService } from '../../../service/auth/token';
import { Post, Comment, ReactionType, ReactionsCount } from '../../../models/posts';

/** All reaction types with their display emoji and label. */
export interface ReactionOption {
  type:  ReactionType;
  emoji: string;
  label: string;
}

export const REACTION_OPTIONS: ReactionOption[] = [
  { type: 'like',  emoji: '👍', label: 'Me gusta' },
  { type: 'love',  emoji: '❤️', label: 'Me encanta' },
  { type: 'haha',  emoji: '😂', label: 'Jaja' },
  { type: 'wow',   emoji: '😮', label: 'Asombro' },
  { type: 'sad',   emoji: '😢', label: 'Tristeza' },
  { type: 'angry', emoji: '😡', label: 'Enojo' },
];

/** Per-comment state bucket for reply lazy-loading and toggle. */
interface ReplyState {
  /** Whether the replies panel is currently visible. */
  expanded: ReturnType<typeof signal<boolean>>;
  /** Whether replies have been fetched at least once (cache guard). */
  loaded:   ReturnType<typeof signal<boolean>>;
  /** Whether a fetch is in progress. */
  loading:  ReturnType<typeof signal<boolean>>;
  /** Fetched replies. */
  replies:  ReturnType<typeof signal<Comment[]>>;
  /** Error message if the fetch failed. */
  error:    ReturnType<typeof signal<string | null>>;
}

@Component({
  selector: 'app-post-item',
  standalone: false,
  templateUrl: './post-item.html',
  styleUrl: './post-item.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PostItem {
  private readonly destroyRef = inject(DestroyRef);

  @Input({ required: true }) post!: Post;
  @Output() postDeleted = new EventEmitter<string>();

  // Expansion state (post-level comments panel)
  expanded = signal(false);

  // Lazy-loaded top-level comments
  comments = signal<Comment[]>([]);
  loadingDetails = signal(false);
  detailsLoaded = signal(false);
  detailsError = signal<string | null>(null);

  // Per-comment reply state — keyed by comment.id
  private readonly replyStateMap = new Map<string, ReplyState>();

  // Comment form
  commentForm: FormGroup;
  submittingComment = signal(false);
  replyingToId = signal<string | null>(null);

  // Comment / reply image attachment
  selectedCommentImage = signal<File | null>(null);
  commentImagePreview = signal<string | null>(null);

  // Post reaction state
  reactingToPost = signal(false);
  myPostReaction = signal<ReactionType | null>(null);
  deletingPost = signal(false);

  // Per-comment/reply reaction state keyed by comment.id
  private readonly commentReactionMap = new Map<string, {
    myReaction: ReturnType<typeof signal<ReactionType | null>>;
    reacting:   ReturnType<typeof signal<boolean>>;
  }>();

  readonly reactionOptions = REACTION_OPTIONS;

  private readonly currentUserId: string | null;

  constructor(
    private postsService: PostsService,
    private tokenService: TokenService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
  ) {
    this.currentUserId = this.tokenService.getCurrentUserId();
    this.commentForm = this.fb.group({
      content: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(2000)]],
    });
  }

  // ---- Comment reaction state accessors ----

  private getOrCreateCommentReactionState(commentId: string) {
    if (!this.commentReactionMap.has(commentId)) {
      this.commentReactionMap.set(commentId, {
        myReaction: signal<ReactionType | null>(null),
        reacting:   signal(false),
      });
    }
    return this.commentReactionMap.get(commentId)!;
  }

  myCommentReaction(commentId: string): ReactionType | null {
    return this.getOrCreateCommentReactionState(commentId).myReaction();
  }

  isReactingToComment(commentId: string): boolean {
    return this.getOrCreateCommentReactionState(commentId).reacting();
  }

  reactionByType(type: ReactionType): ReactionOption {
    return REACTION_OPTIONS.find(o => o.type === type)!;
  }

  // ---- Reply state accessors (create lazily so we never touch Map in template) ----

  private getOrCreateReplyState(commentId: string): ReplyState {
    if (!this.replyStateMap.has(commentId)) {
      this.replyStateMap.set(commentId, {
        expanded: signal(false),
        loaded:   signal(false),
        loading:  signal(false),
        replies:  signal<Comment[]>([]),
        error:    signal<string | null>(null),
      });
    }
    return this.replyStateMap.get(commentId)!;
  }

  /** Called from template for each top-level comment. */
  replyState(commentId: string): ReplyState {
    return this.getOrCreateReplyState(commentId);
  }

  // ---- Expansion / lazy load ----

  toggleExpanded(): void {
    const nowExpanded = !this.expanded();
    this.expanded.set(nowExpanded);

    if (nowExpanded && !this.detailsLoaded()) {
      this.fetchDetails();
    }
  }

  private fetchDetails(): void {
    this.loadingDetails.set(true);
    this.detailsError.set(null);

    this.postsService.listComments(this.post.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          // Backend already returns only root comments (parent_comment_id === null).
          // Ensure any stale reply states for removed comments are cleaned up.
          const incomingIds = new Set(res.comments.map(c => c.id));
          for (const id of this.replyStateMap.keys()) {
            if (!incomingIds.has(id)) {
              this.replyStateMap.delete(id);
            }
          }
          this.comments.set(res.comments);
          this.detailsLoaded.set(true);
          this.loadingDetails.set(false);
        },
        error: () => {
          this.detailsError.set('No se pudieron cargar los comentarios.');
          this.loadingDetails.set(false);
        },
      });
  }

  retryLoadDetails(): void {
    this.fetchDetails();
  }

  // ---- Reply toggle / lazy load ----

  toggleReplies(commentId: string): void {
    const state = this.getOrCreateReplyState(commentId);
    const nowExpanded = !state.expanded();
    state.expanded.set(nowExpanded);

    // Only fetch on the very first expansion; subsequent toggles are instant.
    if (nowExpanded && !state.loaded()) {
      this.fetchReplies(commentId, state);
    }
  }

  private fetchReplies(commentId: string, state: ReplyState): void {
    state.loading.set(true);
    state.error.set(null);

    this.postsService.listReplies(this.post.id, commentId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          state.replies.set(res.replies);
          state.loaded.set(true);
          state.loading.set(false);
        },
        error: () => {
          state.error.set('No se pudieron cargar las respuestas.');
          state.loading.set(false);
        },
      });
  }

  retryLoadReplies(commentId: string): void {
    const state = this.getOrCreateReplyState(commentId);
    this.fetchReplies(commentId, state);
  }

  // ---- Comments ----

  setReplyTarget(commentId: string | null): void {
    this.replyingToId.set(commentId);
    this.commentForm.reset();
    this.clearCommentImage();
  }

  onCommentImageSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedCommentImage.set(file);
    if (file) {
      const reader = new FileReader();
      reader.onload = () => this.commentImagePreview.set(reader.result as string);
      reader.readAsDataURL(file);
    } else {
      this.commentImagePreview.set(null);
    }
    // Reset so the same file can be re-selected after clearing.
    input.value = '';
  }

  clearCommentImage(): void {
    this.selectedCommentImage.set(null);
    this.commentImagePreview.set(null);
  }

  submitComment(): void {
    if (this.commentForm.invalid) {
      this.commentForm.markAllAsTouched();
      return;
    }

    this.submittingComment.set(true);
    const content: string = this.commentForm.get('content')!.value;
    const parentId = this.replyingToId() ?? undefined;
    const image = this.selectedCommentImage() ?? undefined;

    this.postsService.createComment(this.post.id, content, parentId, image)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          const newComment = res.comment;

          if (parentId) {
            // It's a reply — append it to the parent's reply list so the user
            // sees it immediately. If the parent's reply panel wasn't loaded yet,
            // mark it as loaded so toggling won't re-fetch and clobber it.
            const state = this.getOrCreateReplyState(parentId);
            state.replies.update(current => [...current, newComment]);
            state.loaded.set(true);
            state.expanded.set(true);
          } else {
            // Top-level comment — prepend to the main list.
            this.comments.update(current => [newComment, ...current]);
          }

          this.post = { ...this.post, comments_count: this.post.comments_count + 1 };
          this.submittingComment.set(false);
          this.replyingToId.set(null);
          this.commentForm.reset();
          this.clearCommentImage();
          this.snackBar.open('Comentario agregado.', 'Cerrar', { duration: 2500 });
        },
        error: () => {
          this.submittingComment.set(false);
          this.snackBar.open('Error al agregar el comentario.', 'Cerrar', { duration: 3500 });
        },
      });
  }

  deleteComment(commentId: string, parentCommentId: string | null = null): void {
    this.postsService.deleteComment(this.post.id, commentId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          if (parentCommentId) {
            // Remove from the parent's reply list.
            const state = this.replyStateMap.get(parentCommentId);
            if (state) {
              state.replies.update(current => current.filter(r => r.id !== commentId));
            }
          } else {
            // Remove from top-level list and clean up its reply and reaction state.
            this.comments.update(current => current.filter(c => c.id !== commentId));
            this.replyStateMap.delete(commentId);
            this.commentReactionMap.delete(commentId);
          }
          this.post = { ...this.post, comments_count: Math.max(0, this.post.comments_count - 1) };
          this.snackBar.open('Comentario eliminado.', 'Cerrar', { duration: 2500 });
        },
        error: () => {
          this.snackBar.open('Error al eliminar el comentario.', 'Cerrar', { duration: 3500 });
        },
      });
  }

  // ---- Reactions on post ----

  reactToPost(type: ReactionType): void {
    if (this.reactingToPost()) return;
    this.reactingToPost.set(true);
    const prev = this.myPostReaction();

    if (prev === type) {
      // Same reaction clicked — toggle it off
      this.postsService.removePostReaction(this.post.id)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: () => {
            this.post = {
              ...this.post,
              reactions_count: {
                ...this.post.reactions_count,
                [type]: Math.max(0, this.post.reactions_count[type] - 1),
              },
            };
            this.myPostReaction.set(null);
            this.reactingToPost.set(false);
          },
          error: () => {
            this.reactingToPost.set(false);
            this.snackBar.open('Error al quitar la reacción.', 'Cerrar', { duration: 3000 });
          },
        });
    } else {
      // New reaction or switching from another type
      this.postsService.reactToPost(this.post.id, type)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (res) => {
            this.reactingToPost.set(false);
            if (res.action === 'unchanged') return;
            const updated = { ...this.post.reactions_count };
            if (res.action === 'updated' && prev) {
              updated[prev] = Math.max(0, updated[prev] - 1);
            }
            updated[type] = updated[type] + 1;
            this.post = { ...this.post, reactions_count: updated };
            this.myPostReaction.set(type);
          },
          error: () => {
            this.reactingToPost.set(false);
            this.snackBar.open('Error al reaccionar.', 'Cerrar', { duration: 3000 });
          },
        });
    }
  }

  // ---- Reactions on comments / replies ----

  reactToComment(commentId: string, type: ReactionType, parentCommentId: string | null = null): void {
    const state = this.getOrCreateCommentReactionState(commentId);
    if (state.reacting()) return;
    state.reacting.set(true);
    const prev = state.myReaction();

    const patchCount = (rc: ReactionsCount, oldType: ReactionType | null, newType: ReactionType | null): ReactionsCount => {
      const updated = { ...rc };
      if (oldType) updated[oldType] = Math.max(0, updated[oldType] - 1);
      if (newType) updated[newType] = updated[newType] + 1;
      return updated;
    };

    const applyToComment = (updater: (rc: ReactionsCount) => ReactionsCount): void => {
      if (parentCommentId) {
        const rs = this.replyStateMap.get(parentCommentId);
        if (rs) rs.replies.update(list => list.map(r => r.id === commentId ? { ...r, reactions_count: updater(r.reactions_count) } : r));
      } else {
        this.comments.update(list => list.map(c => c.id === commentId ? { ...c, reactions_count: updater(c.reactions_count) } : c));
      }
    };

    if (prev === type) {
      // Toggle off
      this.postsService.removeCommentReaction(this.post.id, commentId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: () => {
            applyToComment(rc => patchCount(rc, type, null));
            state.myReaction.set(null);
            state.reacting.set(false);
          },
          error: () => {
            state.reacting.set(false);
            this.snackBar.open('Error al quitar la reacción.', 'Cerrar', { duration: 3000 });
          },
        });
    } else {
      this.postsService.reactToComment(this.post.id, commentId, type)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (res) => {
            state.reacting.set(false);
            if (res.action === 'unchanged') return;
            applyToComment(rc => patchCount(rc, res.action === 'updated' ? prev : null, type));
            state.myReaction.set(type);
          },
          error: () => {
            state.reacting.set(false);
            this.snackBar.open('Error al reaccionar.', 'Cerrar', { duration: 3000 });
          },
        });
    }
  }

  // ---- Delete post ----

  deletePost(): void {
    if (this.deletingPost()) return;
    this.deletingPost.set(true);

    this.postsService.deletePost(this.post.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.deletingPost.set(false);
          this.postDeleted.emit(this.post.id);
        },
        error: () => {
          this.deletingPost.set(false);
          this.snackBar.open('Error al eliminar la publicacion.', 'Cerrar', { duration: 3500 });
        },
      });
  }

  // ---- Helpers ----

  get totalReactions(): number {
    const rc = this.post.reactions_count;
    return rc.like + rc.love + rc.haha + rc.wow + rc.sad + rc.angry;
  }

  /** Returns a short summary like "5 me gusta · 2 love" for non-zero types. */
  get reactionSummary(): string {
    const rc = this.post.reactions_count;
    const parts: string[] = [];
    for (const opt of this.reactionOptions) {
      const count = rc[opt.type];
      if (count > 0) {
        parts.push(`${count} ${opt.label.toLowerCase()}`);
      }
    }
    return parts.join(' · ');
  }

  formatDate(iso: string | null): string {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('es', {
      year:   'numeric',
      month:  'short',
      day:    'numeric',
      hour:   '2-digit',
      minute: '2-digit',
    });
  }

  isOwner(authorId: string): boolean {
    return !!this.currentUserId && this.currentUserId === authorId;
  }

  trackByCommentId(_index: number, comment: Comment): string {
    return comment.id;
  }

  getCommentReactionSummary(comment: Comment): string {
    const rc = comment.reactions_count;
    const total = rc.like + rc.love + rc.haha + rc.wow + rc.sad + rc.angry;
    return total > 0 ? `${total} reaccion${total === 1 ? '' : 'es'}` : '';
  }
}
