require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 5000;

// ✅ Enable CORS (Allow frontend to call backend)
app.use(cors());
app.use(express.json()); // Parse JSON data

// ✅ Connect to MongoDB
mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log("MongoDB Connected"))
    .catch(err => console.error("MongoDB Connection Error:", err));

// ✅ Contact Schema
const contactSchema = new mongoose.Schema({
    name: String,
    email: String,
    message: String,
});
const Contact = mongoose.model("Contact", contactSchema);

// ✅ POST Route - Save Message to Database
app.post("/api/contact", async (req, res) => {
    try {
        const { name, email, message } = req.body;
        if (!name || !email || !message) {
            return res.status(400).json({ error: "All fields are required" });
        }

        const newContact = new Contact({ name, email, message });
        await newContact.save();
        res.status(201).json({ message: "Message sent successfully!" });
    } catch (error) {
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// ✅ GET Route - Retrieve Messages
app.get("/api/contact", async (req, res) => {
    try {
        const messages = await Contact.find();
        res.json(messages);
    } catch (error) {
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// ✅ Start Server
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
