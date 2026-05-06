import { NgModule } from '@angular/core';

import { SharedImportModule } from '../../shared-import/shared-import-module';
import { SharedModule } from '../shared/shared.module';
import { UsersRoutingModule } from './users-routing-module';

import { UsersManager } from './users-manager/users-manager';
import { UserView } from './user-view/user-view';

@NgModule({
  declarations: [
    UsersManager,
    UserView,
  ],
  imports: [
    SharedImportModule,
    SharedModule,
    UsersRoutingModule,
  ],
})
export class UsersModule {}
