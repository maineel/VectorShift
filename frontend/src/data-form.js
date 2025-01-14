import { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from "@mui/material";
import axios from "axios";

const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  HubSpot: "hubspot",
};

const hubspotScopes = [
  { label: "Contacts", value: "crm/v3/objects/contacts" },
  { label: "Companies", value: "crm/v3/objects/companies" },
  { label: "Deals", value: "crm/v3/objects/deals" },
];

export const DataForm = ({ integrationType, credentials }) => {
  const [loadedData, setLoadedData] = useState([]);
  const [selectedScope, setSelectedScope] = useState(); 
  const endpoint = endpointMapping[integrationType];

  const handleLoad = async () => {
    try {
      const response = await axios.post(
        `http://localhost:8000/integrations/${endpoint}/get_${endpoint}_items`,
        null,
        {
          params: {
            credentials,
            scope: selectedScope,
          },
        }
      );
      setLoadedData(response.data);
    } catch (e) {
      alert(e?.response?.data?.detail);
    }
  };

  return (
    <Box display="flex" flexDirection="column" alignItems="center" width="100%">
      <FormControl sx={{ mt: 2, width: "300px" }}>
        <InputLabel>Select Scope</InputLabel>
        <Select
          value={selectedScope}
          onChange={(e) => setSelectedScope(e.target.value)}
          label="Select Scope"
        >
          {hubspotScopes.map((scope) => (
            <MenuItem key={scope.value} value={scope.value}>
              {scope.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button onClick={handleLoad} sx={{ mt: 2 }} variant="contained">
        Load Data
      </Button>
      <Button onClick={() => setLoadedData([])} sx={{ mt: 1 }} variant="contained">
        Clear Data
      </Button>

      <Box mt={2} width="100%">
        {selectedScope && loadedData.length === 0 && <Typography variant="h6">No data loaded for the chosen scope</Typography>}
        {selectedScope && loadedData.map((item) => (
          <Card key={item.id} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6">ID: {item.id}</Typography>
              <Typography variant="body1">Name: {item.name}</Typography>
              <Typography variant="body2">Email: {item.properties.email}</Typography>
              <Typography variant="body2">Created Date: {item.properties.createdate}</Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};
