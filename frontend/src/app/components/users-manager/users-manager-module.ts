import { NgModule } from '@angular/core';
import { SharedImportModule } from '../../shared-import/shared-import-module';

import { UsersManagerRoutingModule } from './users-manager-routing-module';
import { UsersManager } from './users-manager';

@NgModule({
  declarations: [UsersManager],
  imports: [
    SharedImportModule,
    UsersManagerRoutingModule,
  ],
})
export class UsersManagerModule {}
