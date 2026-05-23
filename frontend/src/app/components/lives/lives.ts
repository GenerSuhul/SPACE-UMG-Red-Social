import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  inject,
} from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { LivesService } from '../../service/lives/lives';
import { TokenService } from '../../service/auth/token';
import { UsersService } from '../../service/users/users';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-lives',
  standalone: false,
  templateUrl: './lives.html',
  styleUrl: './lives.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Lives implements OnInit, OnDestroy {
  private readonly livesService = inject(LivesService);
  private readonly tokenService = inject(TokenService);
  private readonly usersService = inject(UsersService);
  private readonly snackBar     = inject(MatSnackBar);
  private readonly cdr          = inject(ChangeDetectorRef);

  activeLives: any[] = [];
  currentStream: any = null;
  myStream: any = null; // Si yo soy el creador

  titleControl = new FormControl('', { nonNullable: true, validators: [Validators.required] });
  commentControl = new FormControl('', { nonNullable: true });

  chatMessages: any[] = [];
  viewersCount = 0;
  myUsername = 'tú';

  private heartbeatSubscription?: Subscription;
  private listSubscription?: Subscription;
  private userSubscription?: Subscription;
  private ws: WebSocket | null = null;

  // Video de stock que emula la transmisión de webcam del creador
  simulatedStreamUrl = 'https://assets.mixkit.co/videos/preview/mixkit-hand-holding-a-smartphone-in-vertical-position-39934-large.mp4';
  
  ngOnInit(): void {
    this.loadActiveLives();

    // Subscribe to current user's username
    this.userSubscription = this.usersService.currentUser$.subscribe(user => {
      if (user) {
        this.myUsername = user.username;
      }
    });

    // Poll active streams list every 5 seconds
    this.listSubscription = interval(5000).subscribe(() => {
      this.loadActiveLives();
    });
  }

  ngOnDestroy(): void {
    this.stopHeartbeat();
    this.closeWebSocket();
    this.listSubscription?.unsubscribe();
    this.userSubscription?.unsubscribe();
  }

  loadActiveLives(): void {
    this.livesService.listActiveLives().subscribe({
      next: (res) => {
        if (res.ok) {
          this.activeLives = res.streams;
          this.cdr.markForCheck();
        }
      }
    });
  }

  isStreamOwner(): boolean {
    return !!this.currentStream && this.currentStream.creator_username === this.myUsername;
  }

  private connectWebSocket(streamId: string): void {
    this.closeWebSocket();
    try {
      this.ws = new WebSocket('ws://localhost:8888');
      
      this.ws.onopen = () => {
        const joinPayload = {
          type: 'join',
          streamId: streamId,
          username: this.myUsername
        };
        this.ws?.send(JSON.stringify(joinPayload));
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.username && data.content) {
            this.chatMessages = [
              ...this.chatMessages,
              {
                username: data.username,
                content: data.content,
                created_at: data.created_at || new Date().toISOString()
              }
            ];
            this.cdr.markForCheck();
            this.scrollToBottom();
          }
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
      };

      this.ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
    } catch (ex) {
      console.error('Failed to create WebSocket:', ex);
    }
  }

  private closeWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  startSimulatedLive(): void {
    const title = this.titleControl.value.trim() || 'Transmisión de SPACE UMG';
    this.titleControl.reset();

    this.livesService.startLive(title).subscribe({
      next: (res) => {
        if (res.ok) {
          this.myStream = res.stream;
          this.currentStream = res.stream;
          this.chatMessages = [
            { username: 'SPACE UMG', content: '¡Tu transmisión en vivo ha iniciado!', created_at: new Date().toISOString() }
          ];
          this.viewersCount = 1;
          this.cdr.markForCheck();

          this.startHeartbeat(res.stream.id);
          this.connectWebSocket(res.stream.id);
          this.snackBar.open('¡Estás en vivo!', 'Cerrar', { duration: 3000 });
        }
      }
    });
  }

  joinLive(stream: any): void {
    this.currentStream = stream;
    this.myStream = null;
    this.chatMessages = [
      { username: 'SPACE UMG', content: `Te has unido al directo de @${stream.creator_username}`, created_at: new Date().toISOString() }
    ];
    this.viewersCount = stream.viewers_count;
    this.cdr.markForCheck();

    this.startHeartbeat(stream.id);
    this.connectWebSocket(stream.id);
  }

  endMyLive(): void {
    const streamId = this.currentStream?.id || this.myStream?.id;
    if (!streamId) return;

    this.livesService.endLive(streamId).subscribe({
      next: (res) => {
        if (res.ok) {
          this.snackBar.open('Transmisión finalizada.', 'Cerrar', { duration: 3000 });
          this.stopHeartbeat();
          this.closeWebSocket();
          this.currentStream = null;
          this.myStream = null;
          this.loadActiveLives();
          this.cdr.markForCheck();
        }
      }
    });
  }

  leaveLive(): void {
    this.stopHeartbeat();
    this.closeWebSocket();
    this.currentStream = null;
    this.cdr.markForCheck();
  }

  sendComment(): void {
    const text = this.commentControl.value.trim();
    if (!text) return;

    this.commentControl.reset();
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const commentPayload = {
        type: 'comment',
        content: text
      };
      this.ws.send(JSON.stringify(commentPayload));
    } else {
      this.chatMessages = [
        ...this.chatMessages,
        { username: this.myUsername, content: text, created_at: new Date().toISOString() }
      ];
      this.cdr.markForCheck();
      this.scrollToBottom();
    }
  }


  private startHeartbeat(streamId: string): void {
    this.stopHeartbeat();

    this.heartbeatSubscription = interval(3000).subscribe(() => {
      this.livesService.sendHeartbeat(streamId).subscribe({
        next: (res) => {
          if (res.ok) {
            this.viewersCount = res.stream.viewers_count;
            this.cdr.markForCheck();
          }
        },
        error: () => {
          // El stream terminó
          this.stopHeartbeat();
          this.closeWebSocket();
          this.currentStream = null;
          this.myStream = null;
          this.snackBar.open('Esta transmisión ha finalizado.', 'Cerrar', { duration: 3000 });
          this.loadActiveLives();
          this.cdr.markForCheck();
        }
      });
    });
  }

  private stopHeartbeat(): void {
    this.heartbeatSubscription?.unsubscribe();
    this.heartbeatSubscription = undefined;
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const container = document.querySelector('.live-chat-messages');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }, 50);
  }
}
