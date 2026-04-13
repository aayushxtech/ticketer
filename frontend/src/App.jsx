import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import UserDashboard from './pages/UserDashboard';
import BookingPage from './pages/BookingPage';
import AdminDashboard from './pages/AdminDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/user" element={<UserDashboard />} />
        <Route path="/user/show/:showId" element={<BookingPage />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
