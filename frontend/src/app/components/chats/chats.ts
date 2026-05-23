import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  inject,
  signal,
} from '@angular/core';
import { FormControl } from '@angular/forms';
import { TokenService } from '../../service/auth/token';
import { ChatsService } from '../../service/chats/chats';
import { UsersService } from '../../service/users/users';
import { UploadService } from '../../service/upload';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription, interval, startWith } from 'rxjs';

@Component({
  selector: 'app-chats',
  standalone: false,
  templateUrl: './chats.html',
  styleUrl: './chats.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Chats implements OnInit, OnDestroy {
  private readonly chatsService = inject(ChatsService);
  private readonly tokenService = inject(TokenService);
  private readonly usersService = inject(UsersService);
  private readonly uploadService = inject(UploadService);
  private readonly snackBar     = inject(MatSnackBar);
  private readonly cdr          = inject(ChangeDetectorRef);

  myId = '';
  chats: any[] = [];
  activeChat: any = null;
  messages: any[] = [];
  messageControl = new FormControl('', { nonNullable: true });

  // Contacts and selected tab features
  selectedTab = signal<'chats' | 'contacts'>('chats');
  contacts: any[] = [];
  loadingContacts = signal(false);

  // R2 Multimedia upload state
  uploadingMedia = false;
  uploadProgress = 0;

  private pollSubscription?: Subscription;

  ngOnInit(): void {
    this.myId = this.tokenService.getCurrentUserId() || '';
    this.loadChats();
    this.loadContacts();

    // Poll chats list and active messages every 3 seconds to emulate real-time
    this.pollSubscription = interval(3000)
      .pipe(startWith(0))
      .subscribe(() => {
        this.loadChatsSilently();
        if (this.activeChat) {
          this.loadMessagesSilently(this.activeChat.id);
        }
      });
  }

  ngOnDestroy(): void {
    this.pollSubscription?.unsubscribe();
  }

  loadChats(): void {
    this.chatsService.listMyChats().subscribe({
      next: (res) => {
        if (res.ok) {
          this.chats = res.chats;
          this.cdr.markForCheck();
        }
      },
    });
  }

  loadChatsSilently(): void {
    this.chatsService.listMyChats().subscribe({
      next: (res) => {
        if (res.ok) {
          // Mantener el chat seleccionado y actualizar el estado
          const updatedChats = res.chats;
          this.chats = updatedChats;
          if (this.activeChat) {
            const currentActive = updatedChats.find((c: any) => c.id === this.activeChat.id);
            if (currentActive) {
              this.activeChat = currentActive;
            }
          }
          this.cdr.markForCheck();
        }
      },
    });
  }

  selectChat(chat: any): void {
    this.activeChat = chat;
    this.messages = [];
    this.cdr.markForCheck();

    this.chatsService.listMessages(chat.id).subscribe({
      next: (res) => {
        if (res.ok) {
          this.messages = res.messages;
          this.cdr.markForCheck();
          this.scrollToBottom();
          this.markAsRead(chat.id);
        }
      },
    });
  }

  loadMessagesSilently(chatId: string): void {
    this.chatsService.listMessages(chatId).subscribe({
      next: (res) => {
        if (res.ok) {
          const hasNewMessages = res.messages.length !== this.messages.length;
          this.messages = res.messages;
          this.cdr.markForCheck();
          if (hasNewMessages) {
            this.scrollToBottom();
            this.markAsRead(chatId);
          }
        }
      },
    });
  }

  sendMessage(): void {
    const text = this.messageControl.value.trim();
    if (!text || !this.activeChat) return;

    this.messageControl.reset();
    
    // Optimistic UI update
    const tempMessage = {
      id: 'temp-' + Date.now(),
      chat_id: this.activeChat.id,
      sender_id: this.myId,
      content: text,
      is_read: false,
      created_at: new Date().toISOString()
    };
    this.messages = [...this.messages, tempMessage];
    this.cdr.markForCheck();
    this.scrollToBottom();

    this.chatsService.sendMessage(this.activeChat.id, text).subscribe({
      next: (res) => {
        if (res.ok) {
          // Reemplazar mensaje temporal con el real del servidor
          this.messages = this.messages.map((m) => m.id === tempMessage.id ? res.message : m);
          this.cdr.markForCheck();
          this.loadChats();
        }
      },
    });
  }

  markAsRead(chatId: string): void {
    this.chatsService.markRead(chatId).subscribe();
  }

  scrollToBottom(): void {
    setTimeout(() => {
      const container = document.querySelector('.chat-history');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }, 50);
  }

  getAvatarSrc(user: any): string {
    if (user.avatar_url) {
      return user.avatar_url;
    }
    if (user.avatar_base64 && user.avatar_mime) {
      return `data:${user.avatar_mime};base64,${user.avatar_base64}`;
    }
    return 'assets/images/default-avatar.png'; // default avatar placeholder
  }

  // ── CHAT MULTIMEDIA ATTACHMENTS ──

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (!file || !this.activeChat) return;

    // Limit to 15MB (as per requirement upload_chat_media is 15MB limit)
    const limitBytes = 15 * 1024 * 1024;
    if (file.size > limitBytes) {
      this.snackBar.open('El archivo excede el límite permitido de 15MB.', 'Cerrar', { duration: 4000 });
      return;
    }

    // Validate allowed mime types
    const allowedImages = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    const allowedVideos = ['video/mp4', 'video/quicktime', 'video/webm'];
    const isImg = allowedImages.includes(file.type);
    const isVid = allowedVideos.includes(file.type);

    if (!isImg && !isVid) {
      this.snackBar.open('Formato no soportado en chat. Use imágenes o videos.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.uploadingMedia = true;
    this.uploadProgress = 0;
    this.cdr.markForCheck();

    this.uploadService.uploadFile(file, 'chat').subscribe({
      next: (ev: any) => {
        if (ev.type === 1 && ev.total) { // HttpEventType.UploadProgress is 1
          this.uploadProgress = Math.round((ev.loaded / ev.total) * 100);
          this.cdr.markForCheck();
        } else if (ev.type === 4) { // HttpEventType.Response is 4
          if (ev.body && ev.body.ok && ev.body.url) {
            const mediaUrl = ev.body.url;
            const mediaType = isImg ? 'image' : 'video';
            this.sendMediaMessage(mediaUrl, mediaType);
          }
        }
      },
      error: (err: any) => {
        this.uploadingMedia = false;
        this.cdr.markForCheck();
        this.snackBar.open('Error al subir multimedia a R2: ' + (err.error?.errors?.[0]?.message || err.message), 'Cerrar', { duration: 5000 });
      }
    });
    input.value = '';
  }

  private sendMediaMessage(mediaUrl: string, mediaType: string): void {
    const text = ''; // Empty text content for purely multimedia attachments
    const tempMessage = {
      id: 'temp-' + Date.now(),
      chat_id: this.activeChat.id,
      sender_id: this.myId,
      content: text,
      media_url: mediaUrl,
      media_type: mediaType,
      is_read: false,
      created_at: new Date().toISOString()
    };
    
    this.messages = [...this.messages, tempMessage];
    this.uploadingMedia = false;
    this.cdr.markForCheck();
    this.scrollToBottom();

    this.chatsService.sendMessage(this.activeChat.id, text, mediaUrl, mediaType).subscribe({
      next: (res) => {
        if (res.ok) {
          // Replace temp placeholder with actual server stored message
          this.messages = this.messages.map((m) => m.id === tempMessage.id ? res.message : m);
          this.cdr.markForCheck();
          this.loadChats();
        }
      },
      error: () => {
        this.messages = this.messages.filter((m) => m.id !== tempMessage.id);
        this.cdr.markForCheck();
        this.snackBar.open('No se pudo enviar el archivo multimedia.', 'Cerrar', { duration: 3000 });
      }
    });
  }

  loadContacts(): void {
    this.loadingContacts.set(true);
    this.usersService.getMyFollows().subscribe({
      next: (res) => {
        if (res.ok) {
          // Merge both following and followers, and filter out self (just in case)
          const contactMap = new Map<string, any>();
          (res.following || []).forEach((u: any) => {
            if (u.id !== this.myId) contactMap.set(u.id, u);
          });
          (res.followers || []).forEach((u: any) => {
            if (u.id !== this.myId) contactMap.set(u.id, u);
          });
          this.contacts = Array.from(contactMap.values());
          this.cdr.markForCheck();
        }
        this.loadingContacts.set(false);
      },
      error: () => {
        this.loadingContacts.set(false);
      }
    });
  }

  startChatWith(userId: string): void {
    this.chatsService.getOrCreateChat(userId).subscribe({
      next: (res) => {
        if (res && res.ok) {
          this.loadChats();
          // Force active chat selection
          this.activeChat = res.chat;
          this.selectedTab.set('chats');
          this.selectChat(res.chat);
        }
      },
      error: () => {
        this.snackBar.open('No se pudo iniciar el chat con el alumno.', 'Cerrar', { duration: 4000 });
      }
    });
  }
}
