import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import TalkPage from './pages/TalkPage'
import NewTalkPage from './pages/NewTalkPage'

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/talks/new" element={<NewTalkPage />} />
        <Route path="/talks/:id" element={<TalkPage />} />
      </Routes>
    </div>
  )
}
