require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bodyParser = require("body-parser");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();
const PORT = 9090;

// Middleware
app.use(cors());
app.use(express.json()); // ✅ Use express.json() for request parsing
app.use(bodyParser.json());

// Connect to MongoDB
mongoose.connect("mongodb+srv://Ridhi:Yash2106@cluster0.iyssd.mongodb.net/G12")
  .then(() => console.log("✅ MongoDB Connected"))
  .catch(err => console.log("❌ MongoDB Connection Error:", err));

// Define User Schema
const userSchema = new mongoose.Schema({
  name: String,
  email: String,
  password: String
});

const User = mongoose.model("User", userSchema);

// ✅ Handle User Signup Route
app.post("/signup", async (req, res) => {
  console.log("📩 Signup Request Received:", req.body); // Debug log

  const { name, email, password } = req.body;

  try {
    // Check if user already exists
    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({ message: "User already exists" });
    }

    // Hash the password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    // Create new user
    user = new User({
      name,
      email,
      password: hashedPassword
    });

    await user.save();

    console.log("✅ User Registered:", user.email);

    res.status(201).json({ message: "User registered successfully", user });
  } catch (error) {
    console.error("❌ Signup Error:", error);
    res.status(500).json({ message: "Server Error", error });
  }
});

// ✅ Handle User Sign-In Route
app.post("/signin", async (req, res) => {
  console.log("📩 Sign-In Request Received:", req.body);

  const { email, password } = req.body;

  try {
    let user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ message: "User does not exist" });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: "Invalid credentials" });
    }

    console.log("✅ User Signed In:", user.email);

    // Send success response
    res.status(200).json({ message: "Sign-in successful", redirect: "/index.html" });
  } catch (error) {
    console.error("❌ Sign-in Error:", error);
    res.status(500).json({ message: "Server Error", error });
  }
});


// ✅ Start Server
app.listen(PORT, () => {
  console.log(`🚀 Server is running on port ${PORT}`);
});
