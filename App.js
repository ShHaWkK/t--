import React, { useState } from "react";
import { motion } from "framer-motion";
import "./App.css";

const PlayerGenerator = () => {
  const [videoUrl, setVideoUrl] = useState("");
  const [ttl, setTtl] = useState("1h");
  const [allowedDomains, setAllowedDomains] = useState("");
  const [requireToken, setRequireToken] = useState(false);
  const [iframeCode, setIframeCode] = useState("");
  const [playerType, setPlayerType] = useState("HLS");
  const [domainsList, setDomainsList] = useState([]);

  const handleAddDomain = () => {
    if (allowedDomains.trim() !== "" && !domainsList.includes(allowedDomains.trim())) {
      setDomainsList([...domainsList, allowedDomains.trim()]);
      setAllowedDomains("");
    }
  };

  const handleRemoveDomain = (domain) => {
    setDomainsList(domainsList.filter((item) => item !== domain));
  };

  const generatePlayer = async () => {
    const payload = {
      video_url: videoUrl,
      ttl,
      allowed_domains: domainsList,
      require_token: requireToken,
      player_type: playerType,
    };

    const response = await fetch("https://player.mondomaine.com/generate-player/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    setIframeCode(`<iframe src="${result.iframe_url}" width="640" height="360" frameborder="0" allowfullscreen></iframe>`);
  };

  return (
    <motion.div className="container" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
      <motion.h1 className="title" animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 2 }}>
        Générateur de Player
      </motion.h1>
      <motion.div className="card" initial={{ y: -20 }} animate={{ y: 0 }} transition={{ duration: 0.5 }}>
        <div className="form-group">
          <input className="input" placeholder="URL Vidéo" value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Durée de vie :</label>
          <select className="select" value={ttl} onChange={(e) => setTtl(e.target.value)}>
            <option value="1h">1 heure</option>
            <option value="6h">6 heures</option>
            <option value="1d">1 jour</option>
            <option value="7d">7 jours</option>
            <option value="unlimited">Illimité</option>
          </select>
        </div>
        <div className="form-group">
          <label>Type de player :</label>
          <select className="select" value={playerType} onChange={(e) => setPlayerType(e.target.value)}>
            <option value="HLS">HLS</option>
            <option value="DASH">DASH</option>
            <option value="MP4">MP4</option>
          </select>
        </div>
        <div className="form-group">
          <input className="input" placeholder="Ajouter un site autorisé" value={allowedDomains} onChange={(e) => setAllowedDomains(e.target.value)} />
          <motion.button className="button" onClick={handleAddDomain} whileHover={{ scale: 1.05 }}>Ajouter</motion.button>
        </div>
        <div className="allowed-domains">
          {domainsList.map((domain, index) => (
            <motion.span key={index} className="allowed-domain" whileHover={{ scale: 1.05 }}>
              {domain} <button onClick={() => handleRemoveDomain(domain)}>❌</button>
            </motion.span>
          ))}
        </div>
        <div className="form-group inline">
          <input
            type="checkbox"
            checked={requireToken}
            onChange={(e) => setRequireToken(e.target.checked)}
          />
          <label>Exiger un token</label>
        </div>

        <motion.button className="button" onClick={generatePlayer} whileHover={{ scale: 1.05 }}>Générer</motion.button>
        {iframeCode && (
          <motion.div className="iframe-container" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
            <div dangerouslySetInnerHTML={{ __html: iframeCode }} />
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default PlayerGenerator;
