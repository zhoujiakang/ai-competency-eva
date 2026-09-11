import React, { useEffect, useState } from "react";
import { authApi } from "../services/api";
import {
  clearSession,
  readRole,
  readToken,
  readUser,
  writeRole,
  writeUser,
} from "./storage";
import { Landing } from "../components/layout/Landing";
import { Shell } from "../components/layout/Shell";
import { AuthPage } from "../pages/auth/AuthPage";
import {
  StudentDashboard,
  TeacherDashboard,
} from "../pages/dashboard/DashboardPages";
import {
  AssessmentPage,
  ResultPage,
} from "../pages/assessment/AssessmentPages";
import {
  StudentClassesPage,
  StudentTasksPage,
  RecordsPage,
  ReportsPage,
} from "../pages/student/StudentPages";
import {
  TeacherClassesPage,
  TeacherQuestionsPage,
  TeacherTasksPage,
} from "../pages/teacher/TeacherPages";
import { ProfilePage } from "../pages/account/AccountPages";
import { StandardsPage } from "../components/AbilityOverview";

export function App() {
  const [screen, setScreen] = useState(() =>
    readToken() ? "dashboard" : "landing",
  );
  const [role, setRole] = useState(() => readRole() || "student");
  const [user, setUser] = useState(readUser);
  const [toast, setToast] = useState("");
  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(""), 3000);
    return () => clearTimeout(timer);
  }, [toast]);
  const go = (nextScreen) => setScreen(nextScreen);
  const login = (nextUser, nextRole) => {
    setUser(nextUser);
    setRole(nextRole);
    writeUser(nextUser);
    writeRole(nextRole);
    go("dashboard");
  };
  const logout = async () => {
    try {
      await authApi.logout();
    } catch {}
    clearSession();
    setUser(null);
    go("landing");
  };
  if (screen === "landing")
    return (
      <Landing
        choose={(nextRole) => {
          setRole(nextRole);
          go("login");
        }}
      />
    );
  if (screen === "login")
    return (
      <AuthPage
        mode="login"
        role={role}
        back={() => go("landing")}
        register={() => go("register")}
        onLogin={login}
        notify={setToast}
      />
    );
  if (screen === "register")
    return (
      <AuthPage
        mode="register"
        role={role}
        back={() => go("login")}
        register={() => go("login")}
        onLogin={login}
        notify={setToast}
      />
    );
  return (
    <Shell
      role={role}
      user={user}
      screen={screen}
      go={go}
      logout={logout}
      toast={toast}
    >
      <Page screen={screen} role={role} user={user} go={go} notify={setToast} />
    </Shell>
  );
}

function Page({ screen, role, user, go, notify }) {
  if (screen === "dashboard")
    return role === "student" ? (
      <StudentDashboard user={user} go={go} notify={notify} />
    ) : (
      <TeacherDashboard user={user} go={go} />
    );
  if (screen === "classes")
    return role === "student" ? (
      <StudentClassesPage go={go} notify={notify} />
    ) : (
      <TeacherClassesPage notify={notify} />
    );
  if (screen === "records") return <RecordsPage go={go} />;
  if (screen === "reports") return <ReportsPage go={go} notify={notify} />;
  if (screen === "standards") return <StandardsPage notify={notify} />;
  if (screen === "profile")
    return <ProfilePage role={role} user={user} notify={notify} />;
  if (screen === "questions")
    return role === "teacher" ? (
      <TeacherQuestionsPage notify={notify} />
    ) : (
      <StudentDashboard user={user} go={go} notify={notify} />
    );
  if (screen === "tasks")
    return role === "student" ? (
      <StudentTasksPage go={go} notify={notify} />
    ) : (
      <TeacherTasksPage notify={notify} />
    );
  if (screen === "assessment")
    return <AssessmentPage go={go} notify={notify} />;
  if (screen === "result") return <ResultPage go={go} />;
  return <StudentDashboard user={user} go={go} />;
}
