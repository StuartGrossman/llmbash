import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';

const firebaseConfig = {
  projectId: "apper-cb3d6",
  databaseURL: "https://apper-cb3d6-default-rtdb.firebaseio.com",
  storageBucket: "apper-cb3d6.appspot.com",
  messagingSenderId: "112661570589726529369",
  appId: "1:112661570589726529369:web:YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
export const database = getDatabase(app); 