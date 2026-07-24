// Vercel API Route for Image Search
// 使用Supabase存储的特征向量进行相似度计算

const { createClient } = require('@supabase/supabase-js');

// 初始化Supabase客户端
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY; // 使用anon key读取权限
const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * 计算余弦相似度
 */
function cosineSimilarity(vec1, vec2) {
    if (!Array.isArray(vec1) || !Array.isArray(vec2)) {
        console.error('Invalid vectors for similarity calculation');
        return 0;
    }

    const dotProduct = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
    const magnitude1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
    const magnitude2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));

    if (magnitude1 === 0 || magnitude2 === 0) return 0;
    return dotProduct / (magnitude1 * magnitude2);
}

/**
 * 提取上传图片的特征（简化版）
 * 注意：这个函数需要调用外部AI服务或简化模型
 */
async function extractFeaturesFromImage(imageBuffer) {
    // 方案1：调用外部AI服务（如Cloudinary AI、Rekognition等）
    // 方案2：使用轻量级模型
    // 方案3：使用颜色直方图等简单特征

    // 临时实现：使用简单的颜色特征（实际应用中需要替换）
    // 这里返回一个placeholder，实际需要真实的特征提取
    throw new Error('Feature extraction requires external AI service');
}

/**
 * 主处理函数
 */
export default async function handler(req, res) {
    // CORS处理
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        // 获取上传的图片
        const formData = req.body;
        // 注意：Vercel serverless函数处理文件上传需要特殊配置

        // 方案：使用base64编码的图片数据
        const { image_data } = req.body;

        if (!image_data) {
            return res.status(400).json({ error: 'No image data provided' });
        }

        // 提取查询图片特征
        // 注意：这里需要实际的特征提取逻辑
        const queryFeatures = await extractFeaturesFromImage(image_data);

        // 从Supabase获取所有产品特征
        const { data: products, error } = await supabase
            .from('products')
            .select('id, category, product_id, filename, image_url, feature_vector');

        if (error) {
            console.error('Supabase query error:', error);
            return res.status(500).json({ error: 'Database query failed' });
        }

        // 计算相似度
        const results = [];
        const threshold = 0.5;

        for (const product of products) {
            const galleryFeatures = JSON.parse(product.feature_vector);
            const similarity = cosineSimilarity(queryFeatures, galleryFeatures);

            if (similarity >= threshold) {
                results.push({
                    product_id: product.product_id,
                    category: product.category,
                    filename: product.filename,
                    image_url: product.image_url,
                    similarity: similarity
                });
            }
        }

        // 按相似度排序
        results.sort((a, b) => b.similarity - a.similarity);

        // 按款号分组，只保留最相似的
        const seenProducts = {};
        const finalResults = [];
        for (const result of results) {
            if (!seenProducts[result.product_id]) {
                seenProducts[result.product_id] = true;
                finalResults.push(result);
            }
        }

        return res.status(200).json({
            found: finalResults.length > 0,
            results: finalResults.slice(0, 10),
            total_searched: products.length
        });

    } catch (error) {
        console.error('Search error:', error);
        return res.status(500).json({
            error: 'Search failed',
            message: error.message
        });
    }
}
