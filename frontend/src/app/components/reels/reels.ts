import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  inject,
} from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { PostsService } from '../../service/posts/posts';
import { UploadService } from '../../service/upload';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute } from '@angular/router';

// Videos simulados de stock en caso de que no haya en la base de datos
const DEFAULT_REELS = [
  {
    id: 'sim-1',
    author_username: 'mario_galvez',
    content: '¡Bienvenidos a SPACE UMG! La red social del futuro de la ingeniería en sistemas.',
    media_urls: ['https://assets.mixkit.co/videos/preview/mixkit-software-developer-working-on-his-computer-34285-large.mp4'],
    reactions_count: { like: 120, love: 45, haha: 2, wow: 15, sad: 0, angry: 0 },
    comments_count: 14
  },
  {
    id: 'sim-2',
    author_username: 'sofia_sistemas',
    content: 'Probando el algoritmo de recomendación de amigos en SPACE UMG. ¡Súper rápido y reactivo!',
    media_urls: ['https://assets.mixkit.co/videos/preview/mixkit-typing-on-a-computer-keyboard-in-close-up-12628-large.mp4'],
    reactions_count: { like: 88, love: 64, haha: 0, wow: 8, sad: 0, angry: 0 },
    comments_count: 9
  },
  {
    id: 'sim-3',
    author_username: 'umg_central',
    content: 'Instalaciones del campus central de la Universidad Mariano Gálvez de Guatemala. ¡Orgullo UMG!',
    media_urls: ['https://assets.mixkit.co/videos/preview/mixkit-holding-a-smartphone-with-a-green-screen-mockup-39933-large.mp4'],
    reactions_count: { like: 340, love: 180, haha: 1, wow: 35, sad: 0, angry: 0 },
    comments_count: 52
  }
];

@Component({
  selector: 'app-reels',
  standalone: false,
  templateUrl: './reels.html',
  styleUrl: './reels.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Reels implements OnInit, OnDestroy {
  private readonly postsService = inject(PostsService);
  private readonly uploadService = inject(UploadService);
  private readonly snackBar     = inject(MatSnackBar);
  private readonly cdr          = inject(ChangeDetectorRef);
  private readonly route        = inject(ActivatedRoute);

  reels: any[] = [];
  showCreateForm = false;
  uploading = false;
  uploadProgress = 0;
  selectedFile: File | null = null;
  selectedFileName = '';
  isMutedGlobal = true;
  
  private observer: IntersectionObserver | null = null;

  reelForm = new FormGroup({
    content: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  ngOnInit(): void {
    this.loadReels();
    this.route.queryParams.subscribe(params => {
      if (params['create'] === 'true') {
        this.showCreateForm = true;
        this.cdr.markForCheck();
      }
    });
  }

  ngOnDestroy(): void {
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  loadReels(): void {
    this.postsService.listReels().subscribe({
      next: (res) => {
        if (res.ok && res.posts.length > 0) {
          this.reels = res.posts;
        } else {
          this.reels = DEFAULT_REELS;
        }
        this.cdr.markForCheck();
        this.initVideoObserver();
      },
      error: () => {
        this.reels = DEFAULT_REELS;
        this.cdr.markForCheck();
        this.initVideoObserver();
      }
    });
  }

  toggleMute(event: Event): void {
    event.stopPropagation();
    this.isMutedGlobal = !this.isMutedGlobal;
    
    // Apply mute state to all video elements currently in the DOM
    const videoElements = document.querySelectorAll('.reel-video');
    videoElements.forEach((el: any) => {
      el.muted = this.isMutedGlobal;
    });
    
    this.snackBar.open(this.isMutedGlobal ? 'Reels silenciados' : 'Sonido activado', 'Cerrar', { duration: 1500 });
    this.cdr.markForCheck();
  }

  private initVideoObserver(): void {
    if (typeof window === 'undefined') return;

    if (this.observer) {
      this.observer.disconnect();
    }

    setTimeout(() => {
      const videoElements = document.querySelectorAll('.reel-video');
      
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const video = entry.target as HTMLVideoElement;
          if (entry.isIntersecting) {
            video.muted = this.isMutedGlobal;
            video.play().catch(err => {
              console.log('Video play blocked:', err);
              // Fallback to muted if play fails due to auto-play rules
              if (!video.muted) {
                video.muted = true;
                video.play().catch(e => console.log('Fallback play blocked:', e));
              }
            });
          } else {
            video.pause();
          }
        });
      }, {
        threshold: 0.6 // 60% visibility plays the video
      });

      videoElements.forEach(el => this.observer?.observe(el));
    }, 500);
  }

  toggleCreate(): void {
    this.showCreateForm = !this.showCreateForm;
    if (!this.showCreateForm) {
      this.reelForm.reset();
      this.selectedFile = null;
      this.selectedFileName = '';
      this.uploading = false;
    }
    this.cdr.markForCheck();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (!file) return;

    // Validate type
    const allowedTypes = ['video/mp4', 'video/quicktime', 'video/webm'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.mp4') && !file.name.endsWith('.mov') && !file.name.endsWith('.webm')) {
      this.snackBar.open('Formato de video no permitido. Use MP4, MOV o WebM.', 'Cerrar', { duration: 4000 });
      return;
    }

    // Validate size (100MB)
    const limitBytes = 100 * 1024 * 1024;
    if (file.size > limitBytes) {
      this.snackBar.open('El video excede el límite permitido de 100MB.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.selectedFile = file;
    this.selectedFileName = file.name;
    this.cdr.markForCheck();
  }

  submitReel(): void {
    if (this.reelForm.invalid || !this.selectedFile) {
      this.snackBar.open('Por favor ingresa una descripción y selecciona un video.', 'Cerrar', { duration: 3000 });
      return;
    }

    this.uploading = true;
    this.uploadProgress = 0;
    this.cdr.markForCheck();

    this.uploadService.uploadFile(this.selectedFile, 'reel').subscribe({
      next: (event: HttpEvent<any>) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.uploadProgress = Math.round((event.loaded / event.total) * 100);
          this.cdr.markForCheck();
        } else if (event.type === HttpEventType.Response) {
          if (event.body && event.body.ok && event.body.url) {
            this.publishReel(event.body.url);
          }
        }
      },
      error: (err) => {
        this.uploading = false;
        this.cdr.markForCheck();
        this.snackBar.open('Error al subir video a R2: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 5000 });
      }
    });
  }

  private publishReel(videoUrl: string): void {
    const content = this.reelForm.value.content || '';
    this.postsService.createReel(content, videoUrl).subscribe({
      next: (res) => {
        if (res.ok) {
          this.snackBar.open('¡Reel publicado con éxito!', 'Cerrar', { duration: 3000 });
          this.reelForm.reset();
          this.selectedFile = null;
          this.selectedFileName = '';
          this.uploading = false;
          this.showCreateForm = false;
          this.loadReels();
          this.cdr.markForCheck();
        }
      },
      error: () => {
        this.uploading = false;
        this.cdr.markForCheck();
        this.snackBar.open('Error al publicar el Reel.', 'Cerrar', { duration: 3000 });
      }
    });
  }

  likeReel(reel: any): void {
    const hasLiked = reel.my_reaction === 'like';
    if (hasLiked) {
      this.postsService.removePostReaction(reel.id).subscribe({
        next: (res) => {
          if (res.ok) {
            reel.my_reaction = null;
            if (!reel.reactions_count) reel.reactions_count = { like: 0 };
            reel.reactions_count.like = Math.max(0, reel.reactions_count.like - 1);
            this.cdr.markForCheck();
            this.snackBar.open('Quitaste tu me gusta', 'Cerrar', { duration: 1500 });
          }
        }
      });
    } else {
      this.postsService.reactToPost(reel.id, 'like').subscribe({
        next: (res) => {
          if (res.ok) {
            reel.my_reaction = 'like';
            if (!reel.reactions_count) reel.reactions_count = { like: 0 };
            reel.reactions_count.like++;
            this.cdr.markForCheck();
            this.snackBar.open('¡Te gustó este Reel!', 'Cerrar', { duration: 1500 });
          }
        }
      });
    }
  }

  getLikesCount(reel: any): number {
    const counts = reel.reactions_count || {};
    return Object.values(counts).reduce((a: any, b: any) => a + b, 0) as number;
  }
}
