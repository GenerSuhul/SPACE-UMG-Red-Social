export interface UserInterface {
  username:      string;
  email:         string;
  age:           number;
  first_name:    string;
  last_name:     string;
  is_active:     boolean;
  avatar_base64: string | null;
  avatar_mime:   string | null;
}

/** Minimal public representation returned by /api/users/search and /api/users/<id>. */
export interface PublicUserInterface {
  id:            string;
  username:      string;
  first_name:    string;
  last_name:     string;
  age:           number;
  avatar_base64: string | null;
  avatar_mime:   string | null;
}

export interface GetUserResponse {
  ok:   boolean;
  user: UserInterface;
}

export interface UpdateAvatarResponse {
  ok:   boolean;
  user: UserInterface;
}

export interface SearchUsersResponse {
  ok:    boolean;
  total: number;
  users: PublicUserInterface[];
}

export interface GetPublicUserResponse {
  ok:   boolean;
  user: PublicUserInterface;
}
