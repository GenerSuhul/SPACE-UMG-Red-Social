export interface UserInterface {
  id?:           string;
  username:      string;
  email:         string;
  age:           number;
  first_name:    string;
  last_name:     string;
  is_active:     boolean;
  avatar_base64: string | null;
  avatar_mime:   string | null;
  avatar_url?:   string | null;
  cover_url?:    string | null;
  cover_base64?: string | null;
  cover_mime?:   string | null;
  followers_count?: number;
  following_count?: number;
}

/** Minimal public representation returned by /api/users/search and /api/users/<id>. */
export interface PublicUserInterface {
  id:              string;
  username:        string;
  first_name:      string;
  last_name:       string;
  age:             number;
  avatar_base64:   string | null;
  avatar_mime:     string | null;
  avatar_url?:     string | null;
  cover_url?:      string | null;
  cover_base64?:   string | null;
  cover_mime?:     string | null;
  is_following?:   boolean;
  followers_count?: number;
  following_count?: number;
}

export interface FollowToggleResponse {
  ok:              boolean;
  action:          'followed' | 'unfollowed';
  target_user:     { id: string; username: string; first_name: string; last_name: string };
  followers_count: number;
  following_count: number;
}

export interface FollowUser {
  id:         string;
  username:   string;
  first_name: string;
  last_name:  string;
}

export interface MyFollowsResponse {
  ok:              boolean;
  followers_count: number;
  following_count: number;
  followers:       FollowUser[];
  following:       FollowUser[];
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
