import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';
import { getAuth } from 'firebase/auth';
import { getAnalytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: "AIzaSyDrxon9VMdyAg3QYafx-Eew8uvoMOCli3g",
  authDomain: "apper-cb3d6.firebaseapp.com",
  databaseURL: "https://apper-cb3d6-default-rtdb.firebaseio.com",
  projectId: "apper-cb3d6",
  storageBucket: "apper-cb3d6.firebasestorage.app",
  messagingSenderId: "462882174662",
  appId: "1:462882174662:web:51ff8c16d5e69ea4d209c7",
  measurementId: "G-TXJLZQK0MV"
};

const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);
export const auth = getAuth(app);
export const analytics = getAnalytics(app); 