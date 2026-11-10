
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const registerUser = (data) => {
  return api.post("/auth/register", data);
};

export const loginUser = (email, password) => {
  const formData = new URLSearchParams();

  formData.append("username", email);
  formData.append("password", password);

  return api.post("/auth/login", formData);
};

export const getBranches = () => {
  return api.get("/hospital/branches");
};

export const getDoctors = () => {
  return api.get("/hospital/doctors");
};

export const getAppointments = (userId) => {
  return api.get("/appointments/", {
    params: { user_id: userId },
  });
};

export default api;

