import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Card,
    CardContent,
    Typography
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState([]);
    const endpoint = endpointMapping[integrationType];
    
    const handleLoad = async () => {
        try {
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/get_hubspot_items`, null, {
                params: {
                    credentials: credentials
                }
            });
            setLoadedData(response.data);
        } catch (e) {   
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData([])}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
                <Box mt={2} width='100%'>
                    {loadedData.map((item) => (
                        <Card key={item.id} sx={{ mb: 2 }}>
                            <CardContent>
                                <Typography variant="h6">ID: {item.id}</Typography>
                                <Typography variant="body1">Name: {item.name}</Typography>
                                <Typography variant="body2">Email: {item.properties.email}</Typography>
                                <Typography variant="body2">First Name: {item.properties.firstname}</Typography>
                                <Typography variant="body2">Last Name: {item.properties.lastname}</Typography>
                                <Typography variant="body2">Created Date: {item.properties.createdate}</Typography>
                                <Typography variant="body2">Last Modified Date: {item.properties.lastmodifieddate}</Typography>
                            </CardContent>
                        </Card>
                    ))}
                </Box>
            </Box>
        </Box>
    );
}
