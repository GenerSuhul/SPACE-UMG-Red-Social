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
  loading  = signal(true);
  notFound = signal(false);
  user     = signal<PublicUserInterface | null>(null);

  private readonly route        = inject(ActivatedRoute);
  private readonly usersService = inject(UsersService);
  private readonly cdr          = inject(ChangeDetectorRef);

  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    // Sin take(1): se re-ejecuta con switchMap cada vez que cambia el parámetro :id,
    // permitiendo que navegar de /users/id1 a /users/id2 recargue reactivamente.
    this.route.paramMap.pipe(
      switchMap(params => {
        const id = params.get('id') ?? '';
        this.loading.set(true);
        this.notFound.set(false);
        this.user.set(null);
        this.cdr.markForCheck();
        return this.usersService.getUserById(id);
      }),
      takeUntil(this.destroy$),
    ).subscribe({
      next: (res) => {
        this.user.set(res.user);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: (err: unknown) => {
        this.loading.set(false);
        const status = (err as { status?: number })?.status;
        if (status === 404) {
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

  get avatarSrc(): string | null {
    const u = this.user();
    if (u?.avatar_base64 && u.avatar_mime) {
      return `data:${u.avatar_mime};base64,${u.avatar_base64}`;
    }
    return null;
  }
}
