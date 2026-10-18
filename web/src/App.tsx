import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router'
import { type Session, useSession } from './auth/session'
import { LoginScreen } from './features/auth/LoginScreen'
import { SignupScreen } from './features/auth/SignupScreen'
import { ControlSheetPage } from './features/controls/ControlSheetPage'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { BatchesPage } from './features/journals/BatchesPage'
import { ChecklistSettingsPage } from './features/journals/ChecklistSettingsPage'
import { ChemicalsPage } from './features/journals/ChemicalsPage'
import { EquipmentPage } from './features/journals/EquipmentPage'
import { EventLogPage } from './features/journals/EventLogPage'
import { JournalsHubPage } from './features/journals/JournalsHubPage'
import { MedicalChecksPage } from './features/journals/MedicalChecksPage'
import { AppShell } from './features/shell/AppShell'
import { routePatterns, routes } from './routes'

// A stored session shows the app, otherwise the login screen (at any URL, so a
// deep link survives sign-in). The session clears itself when a token refresh
// fails, which drops back to login.
function App() {
  const session = useSession()
  return <BrowserRouter>{session === null ? <SignedOut /> : <SignedIn session={session} />}</BrowserRouter>
}

/** /signup shows sign-up; any other URL shows login and stays put, so a deep link survives sign-in. */
function SignedOut() {
  return useLocation().pathname === routes.signup ? <SignupScreen /> : <LoginScreen />
}

function SignedIn({ session }: { session: Session }) {
  return (
    <Routes>
      <Route element={<AppShell session={session} />}>
        <Route index element={<DashboardPage session={session} />} />
        <Route path={routes.daily} element={<ControlSheetPage session={session} period="daily" />} />
        <Route path={routes.journals} element={<JournalsHubPage session={session} />} />
        <Route path={routes.monthly} element={<ControlSheetPage session={session} period="monthly" />} />
        <Route path={routePatterns.eventLog} element={<EventLogPage session={session} />} />
        <Route path={routes.batches} element={<BatchesPage session={session} />} />
        <Route path={routes.medical} element={<MedicalChecksPage session={session} />} />
        <Route path={routes.equipment} element={<EquipmentPage session={session} />} />
        <Route path={routes.chemicals} element={<ChemicalsPage session={session} />} />
        <Route path={routePatterns.checklistSettings} element={<ChecklistSettingsPage session={session} />} />
        <Route path="*" element={<Navigate to={routes.dashboard} replace />} />
      </Route>
    </Routes>
  )
}

export default App
