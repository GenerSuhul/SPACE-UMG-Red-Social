import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './interceptors/auth-interceptor';
import { SharedModule } from './components/shared/shared.module';
import { SharedImportModule } from './shared-import/shared-import-module';
import { Toolbar } from './components/toolbar/toolbar';

@NgModule({
  declarations: [
    App,
    Toolbar,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SharedModule,
    SharedImportModule,
  ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideAnimations(),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
  bootstrap: [App]
})
export class AppModule { }
