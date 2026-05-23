import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './interceptors/auth-interceptor';
import { SharedModule } from './components/shared/shared.module';
import { SharedImportModule } from './shared-import/shared-import-module';
import { Toolbar } from './components/toolbar/toolbar';

import { Chats } from './components/chats/chats';
import { Reels } from './components/reels/reels';
import { Lives } from './components/lives/lives';

@NgModule({
  declarations: [
    App,
    Toolbar,
    Chats,
    Reels,
    Lives,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SharedModule,
    SharedImportModule,
  ],
  providers: [
    provideAnimations(),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
  bootstrap: [App]
})
export class AppModule { }

