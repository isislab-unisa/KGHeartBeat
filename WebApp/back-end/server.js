const express = require('express');
const cors = require('cors');
const { connectToMongoDB } = require('./db');
const knowledge_graph_router = require('./routes/knowledge_graph');
const accessibility = require('./routes/accessibility');
const intrinsic = require('./routes/intrinsic');
const trust = require('./routes/trust');
const dataset_dynamicity = require('./routes/dataset_dynamicity');
const contextual = require('./routes/contextual');
const representational = require('./routes/representational');
const score = require('./routes/score');
const extra = require('./routes/extra');
const upload = require('express-fileupload');

require('dotenv').config();

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
const uploadMiddleware = upload();
app.use((req, res, next) => {
    if (req.path === '/knowledge_graph/evaluate-turtle') {
        return next();
    }
    return uploadMiddleware(req, res, next);
});

app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
});

//TODO: is possible to limitate the use of a middleware only for a specific path request
app.use(async (req, res, next) => {
    // Turtle evaluation is self-contained and does not require MongoDB.
    if (req.path === '/knowledge_graph/evaluate-turtle') {
        return next();
    }
    try {
        req.db = await connectToMongoDB(); // Ottieni la connessione dal pool
        next();
    } catch (error) {
        console.error(error);
        res.status(500).send('Error during the connection to the DB');
    }
});

app.use('/knowledge_graph',knowledge_graph_router);
app.use('/accessibility',accessibility);
app.use('/intrinsic',intrinsic);
app.use('/trust',trust);
app.use('/dataset_dynamicity',dataset_dynamicity);
app.use('/contextual',contextual);
app.use('/representational',representational);
app.use('/score',score);
app.use('/extra',extra);

app.listen(port,() => {
    console.log(`Server is running on port: ${port}`);
})
