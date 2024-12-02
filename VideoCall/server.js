const express = require('express');
const app = express();
const port = 8223;

app.get('/videocall/', (req, res) => {
    const meetingId = req.query.meeting_id;
    const apiKey = req.query.api_key;
    const userName = req.query.user_name;
    const isDoctor = req.query.is_doctor
    const token = req.query.token

    if (!meetingId || !apiKey || !userName || !token || typeof isDoctor === 'undefined') {
        return res.status(400).send('Missing required query parameters');
    }

    let redirectUrl;
    if (isDoctor === 'true') {
        redirectUrl = "https://doctorapp.zapto.org/doctors/doctor_home/?token=${encodeURIComponent(token)}";
    } else {
        redirectUrl = "https://doctorapp.zapto.org/patients/home/?token=${encodeURIComponent(token)}";
    }

    const html = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Doctor App</title>
        </head>
        <body>

            <script>
                var script = document.createElement("script");
                script.type = "text/javascript";

                script.addEventListener("load", function (event) {
                    const config = {
                        name: "${userName}",
                        meetingId: "${meetingId}",
                        apiKey: "${apiKey}",

                        micEnabled: true,
                        webcamEnabled: true,
                        participantCanToggleSelfWebcam: true,
                        participantCanToggleSelfMic: true,

                        chatEnabled: true,
                        screenShareEnabled: true,

                        leftScreen: {
                            actionButton: {
                                label: "Exit",
                                href: "${redirectUrl}",
                            },
                            rejoinButtonEnabled: true,
                        },

                    };

                    const meeting = new VideoSDKMeeting();
                    meeting.init(config);

                });

                script.src = "https://sdk.videosdk.live/rtc-js-prebuilt/0.3.42/rtc-js-prebuilt.js";
                document.getElementsByTagName("head")[0].appendChild(script);
            </script>

        </body>
        </html>
    `;

    res.send(html);
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});

