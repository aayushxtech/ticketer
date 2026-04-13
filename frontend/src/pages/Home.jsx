import { Link } from 'react-router-dom';
import Card from '../components/Card';
import './Home.css';

export default function Home() {
  return (
    <div className="home">
      <h1 className="home__title">Ticket Booking</h1>
      <p className="home__subtitle">Select your role to continue</p>
      <div className="home__roles">
        <Link to="/user" className="home__link">
          <Card className="home__card">
            <h2>User</h2>
            <p className="home__desc">Browse shows and book seats</p>
          </Card>
        </Link>
        <Link to="/admin" className="home__link">
          <Card className="home__card">
            <h2>Admin</h2>
            <p className="home__desc">Manage shows and seat layouts</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
