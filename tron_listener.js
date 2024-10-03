const fetch = require('node-fetch');
const sqlite3 = require('sqlite3').verbose();

const TRONGRID_API = 'https://api.trongrid.io';
const USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
const API_KEY = '926b6106-c126-4a48-8419-2ca0d8009cf9'; // 替换为你的实际 API 密钥

// Initialize SQLite
const db = new sqlite3.Database('./data.sqlite3');

// 缓存的 USDT 地址集合
let cachedAddresses = [];

// 从数据库中加载所有 USDT 地址并缓存
function loadUserAddresses() {
    return new Promise((resolve, reject) => {
        db.all("SELECT usdt_address FROM user WHERE usdt_address IS NOT NULL", (err, rows) => {
            if (err) {
                console.error('Error loading user addresses:', err);
                return reject(err);
            }
            cachedAddresses = rows.map(row => row.usdt_address);
            console.log('Cached addresses:', cachedAddresses);
            resolve(cachedAddresses);
        });
    });
}

// 定义一个函数来监听并处理充值事件
async function checkAndProcessDeposits() {
    try {
        // 确保缓存中有 USDT 地址
        if (cachedAddresses.length === 0) {
            await loadUserAddresses();
        }

        for (const usdt_address of cachedAddresses) {
            console.log(`Checking deposits for address ${usdt_address}`);

            // 使用 TronGrid API 获取该地址的 USDT 转账事件，确保只监听 to 地址，直接查询整个历史交易
            const response = await fetch(`${TRONGRID_API}/v1/accounts/${usdt_address}/transactions/trc20?contract_address=${USDT_CONTRACT}&only_to=true`, {
                headers: {
                    'TRON-PRO-API-KEY': API_KEY
                }
            });

            const data = await response.json();

            if (data.data && data.data.length > 0) {
                for (const event of data.data) {
                    const { transaction_id, value, block_timestamp, to } = event;
                    const amount = value / 1e6;  // USDT 是 6 位小数

                    // 确保交易的 to 地址是我们要处理的目标地址
                    if (to !== usdt_address) {
                        console.log(`Skipping transaction ${transaction_id} for non-matching address ${to}.`);
                        continue;
                    }

                    // 检查该交易哈希是否已经处理过
                    db.get("SELECT COUNT(*) AS count FROM recharge_logs WHERE transaction_hash = ?", [transaction_id], (err, row) => {
                        if (err) {
                            console.error("Error checking recharge log:", err);
                            return;
                        }

                        if (row.count === 0) {
                            // 在插入新充值记录之前，先通过 usdt_address 获取 tg_id
                            db.get("SELECT tg_id FROM user WHERE usdt_address = ?", [usdt_address], (err, row) => {
                                if (err) {
                                    console.error("Error fetching tg_id:", err);
                                    return;
                                }

                                const tg_id = row ? row.tg_id : null;
                                if (tg_id) {
                                    // 插入新充值记录
                                    db.run("INSERT INTO recharge_logs (tg_id, usdt_address, transaction_hash, amount, timestamp, blockchain_status, processed) VALUES (?, ?, ?, ?, ?, ?, 1)",
                                        [tg_id, usdt_address, transaction_id, amount, block_timestamp, 'confirmed'], (err) => {
                                            if (err) {
                                                console.error("Error inserting recharge log:", err);
                                                return;
                                            }

                                            // 更新用户余额
                                            db.run("UPDATE user SET available_balance = available_balance + ? WHERE tg_id = ?", [amount, tg_id], (err) => {
                                                if (err) {
                                                    console.error("Error updating balance:", err);
                                                    return;
                                                }

                                                console.log(`User ${tg_id} balance updated with ${amount} USDT.`);
                                            });
                                        });
                                } else {
                                    console.error(`No tg_id found for address ${usdt_address}, skipping log insertion.`);
                                }
                            });
                        } else {
                            console.log(`Transaction ${transaction_id} already processed.`);
                        }
                    });
                }
            } else {
                console.log(`No deposits found for address ${usdt_address}`);
            }
        }
    } catch (error) {
        console.error('Error in checkAndProcessDeposits:', error);
    }
}

// 定时加载地址，每 5 分钟更新一次缓存
setInterval(loadUserAddresses, 5 * 60 * 1000);

// 设置定时轮询，每 60 秒执行一次
setInterval(checkAndProcessDeposits, 60000);

// 初始加载一次地址
loadUserAddresses();
