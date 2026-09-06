declare module "@firebase/auth" {
  export function getAuth(app?: any): any;
  export class GoogleAuthProvider {
    setCustomParameters(params: Record<string, string>): void;
  }
  export function signInWithPopup(auth: any, provider: any): Promise<any>;
  export function signInWithEmailAndPassword(auth: any, email: string, pass: string): Promise<any>;
  export function createUserWithEmailAndPassword(auth: any, email: string, pass: string): Promise<any>;
  export function sendPasswordResetEmail(auth: any, email: string): Promise<any>;
  export function signOut(auth: any): Promise<any>;
  export function updateProfile(user: any, profile: { displayName?: string; photoURL?: string }): Promise<any>;
  export interface UserCredential {
    user: any;
  }
}
