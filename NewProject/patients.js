const express = require('express');
const router = express.Router();
const Patient = require('./Patient'); // Assuming Patient.js is in the same directory

// GET all patients
router.get('/', async (req, res) => {
  try {
    const patients = await Patient.find();
    res.json(patients);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server Error' });
  }
});

// GET a specific patient by ID
router.get('/:id', async (req, res) => {
  try {
    const patient = await Patient.findById(req.params.id);
    if (!patient) {
      return res.status(404).json({ message: 'Patient not found' });
    }
    res.json(patient);
  } catch (err) {
    console.error(err);
    if (err.kind === 'ObjectId') {
      return res.status(400).json({ message: 'Invalid Patient ID' });
    }
    res.status(500).json({ message: 'Server Error' });
  }
});

// POST a new patient
router.post('/', async (req, res) => {
  const patient = new Patient({
    identifier: req.body.identifier,
    name: req.body.name,
    gender: req.body.gender,
    birthDate: req.body.birthDate,
    // Add other fields as needed
  });

  try {
    const newPatient = await patient.save();
    res.status(201).json(newPatient);
  } catch (err) {
    console.error(err);
    res.status(400).json({ message: err.message });
  }
});

// PUT (update) an existing patient
router.put('/:id', async (req, res) => {
  try {
    const patient = await Patient.findById(req.params.id);

    if (!patient) {
      return res.status(404).json({ message: 'Patient not found' });
    }

    // Update fields
    if (req.body.identifier) patient.identifier = req.body.identifier;
    if (req.body.name) patient.name = req.body.name;
    if (req.body.gender) patient.gender = req.body.gender;
    if (req.body.birthDate) patient.birthDate = req.body.birthDate;
    // Update other fields as needed

    const updatedPatient = await patient.save();
    res.json(updatedPatient);
  } catch (err) {
    console.error(err);
    if (err.kind === 'ObjectId') {
      return res.status(400).json({ message: 'Invalid Patient ID' });
    }
    res.status(500).json({ message: 'Server Error' });
  }
});

// DELETE a patient
router.delete('/:id', async (req, res) => {
  try {
    const patient = await Patient.findByIdAndDelete(req.params.id);
    if (!patient) {
      return res.status(404).json({ message: 'Patient not found' });
    }
    res.json({ message: 'Patient deleted' });
  } catch (err) {
    console.error(err);
    if (err.kind === 'ObjectId') {
      return res.status(400).json({ message: 'Invalid Patient ID' });
    }
    res.status(500).json({ message: 'Server Error' });
  }
});

module.exports = router;