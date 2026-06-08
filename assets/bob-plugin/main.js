function supportLanguages() {
    return ["auto", "zh-Hans", "en"];
}

function ocr(query, completion) {
    // Determine the host (default to localhost:8000)
    var apiUrl = "http://localhost:8000/extract/base64";
    var engine = "auto"; // Default engine (lets server decide)
    
    // Read image data as Base64 string
    var base64Str = query.image.toBase64();
    if (!base64Str) {
        completion({
            error: {
                type: "param",
                message: "Failed to read image data."
            }
        });
        return;
    }

    // Construct JSON payload
    var payload = {
        "base64_data": base64Str,
        "engine": engine
    };

    // Send HTTP POST request
    $http.post({
        url: apiUrl,
        header: {
            "Content-Type": "application/json"
        },
        body: payload,
        handler: function(resp) {
            if (resp.response.statusCode >= 200 && resp.response.statusCode < 300) {
                var data = resp.data;
                var texts = [];
                
                // Parse standard UniOCR Document structure
                if (data.pages && data.pages.length > 0) {
                    var firstPage = data.pages[0];
                    if (firstPage.blocks && firstPage.blocks.length > 0) {
                        for (var i = 0; i < firstPage.blocks.length; i++) {
                            texts.push({
                                text: firstPage.blocks[i].text
                            });
                        }
                    } else if (firstPage.text) {
                        texts.push({
                            text: firstPage.text
                        });
                    }
                } else if (data.text) {
                     texts.push({
                         text: data.text
                     });
                }

                // If nothing was found, return empty array
                if (texts.length === 0) {
                     texts.push({text: ""});
                }

                completion({
                    result: {
                        texts: texts
                    }
                });
            } else {
                var errMsg = "Unknown error";
                if (resp.data && resp.data.detail) {
                    errMsg = resp.data.detail;
                }
                completion({
                    error: {
                        type: "api",
                        message: errMsg,
                        addtion: JSON.stringify(resp.data)
                    }
                });
            }
        }
    });
}
